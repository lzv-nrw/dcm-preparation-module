"""
Preparation View-class definition
"""

from typing import Optional
from shutil import copytree
from pathlib import Path
from functools import partial
import os
from uuid import uuid4

from lxml import etree as ET
from bagit_utils import Bag
from flask import Blueprint, jsonify, Response, request
from data_plumber_http.decorators import flask_handler, flask_args, flask_json
from dcm_common import LoggingContext
from dcm_common.util import get_output_path
from dcm_common.orchestra import JobConfig, JobContext, JobInfo
from dcm_common import services

from dcm_preparation_module.config import AppConfig
from dcm_preparation_module.models import PreparationConfig, Report
from dcm_preparation_module.handlers import get_preparation_handler
from dcm_preparation_module.components import MetadataOperator, ProcessResult


class PreparationView(services.OrchestratedView):
    """View-class for ip-preparation."""

    NAME = "ip-preparation"

    def __init__(self, config: AppConfig, *args, **kwargs) -> None:
        super().__init__(config, *args, **kwargs)

        # initialize MetadataOperator
        self.metadata_operator = MetadataOperator()

    def register_job_types(self):
        self.config.worker_pool.register_job_type(
            self.NAME, self.prepare, Report
        )

    def configure_bp(self, bp: Blueprint, *args, **kwargs) -> None:

        @bp.route("/prepare", methods=["POST"])
        @flask_handler(  # unknown query
            handler=services.no_args_handler,
            json=flask_args,
        )
        @flask_handler(  # process ip-preparation
            handler=get_preparation_handler(cwd=self.config.FS_MOUNT_POINT),
            json=flask_json,
        )
        def prepare(
            preparation: PreparationConfig,
            token: Optional[str] = None,
            callback_url: Optional[str] = None,
        ):
            """Prepare IP for SIP-transformation."""
            try:
                token = self.config.controller.queue_push(
                    token or str(uuid4()),
                    JobInfo(
                        JobConfig(
                            self.NAME,
                            original_body=request.json,
                            request_body={
                                "preparation": preparation.json,
                                "callback_url": callback_url,
                            },
                        ),
                        report=Report(
                            host=request.host_url, args=request.json
                        ),
                    ),
                )
            # pylint: disable=broad-exception-caught
            except Exception as exc_info:
                return Response(
                    f"Submission rejected: {exc_info}",
                    mimetype="text/plain",
                    status=500,
                )

            return jsonify(token.json), 201

        self._register_abort_job(bp, "/prepare")

    @staticmethod
    def load_baginfo(bag: Bag) -> dict:
        """
        Returns contents of 'bag-info.txt'.
        """
        return bag.baginfo

    def apply_baginfo(self, bag: Bag, result: ProcessResult) -> dict:
        """
        Updates contents of `bag.info`.
        """
        bag.set_baginfo(result.metadata)

    @classmethod
    def load_significant_properties(cls, path: Path, ns: str) -> dict:
        """
        Returns existing 'significant_properties.xml'-metadata as dictionary or
        an empty dict if not existing.
        """

        # check conditions
        if not path.is_file():
            return {}

        # parse
        et = ET.fromstring(path.read_text(encoding="utf-8"))
        return cls.load_significant_properties_from_tree(et, ns)

    @staticmethod
    def load_significant_properties_from_tree(
        sig_prop_et: ET._Element, ns: str
    ) -> dict:
        """
        Returns 'significant_properties.xml'-metadata as dictionary.
        """
        # parse
        try:
            significant_properties = sig_prop_et.find(f"{ns}object").findall(
                f"{ns}significantProperties"
            )
        except AttributeError:
            return {}
        result = {}
        for p in significant_properties:
            type_ = p.find(f"{ns}significantPropertiesType")
            value = p.find(f"{ns}significantPropertiesValue")
            if type_ is None or value is None:
                continue
            result[type_.text] = value.text
        return result

    def apply_significant_properties(
        self,
        path: Path,
        sig_prop_et: ET._Element,
        ns: str,
        result: ProcessResult
    ) -> None:
        """
        Updates significant properties metadata and writes the xml file.
        """
        # check conditions
        if not result.metadata:
            return

        # replace values for existing types
        existing_types = []
        for p in sig_prop_et.find(f"{ns}object").findall(
            f"{ns}significantProperties"
        ):
            type_ = p.find(f"{ns}significantPropertiesType")
            value = p.find(f"{ns}significantPropertiesValue")
            if type_ is None or value is None:
                continue
            existing_types.append(type_.text)
            value.text = (
                result.metadata[type_.text]
                if isinstance(result.metadata[type_.text], str)
                else result.metadata[type_.text][0]
            )

        # add values for new types
        new_types = list(
            filter(
                lambda x: x in result.metadata and x not in existing_types,
                self.config.SIGPROP_TYPES,
            )
        )
        if new_types:
            # find the parent and add new elements
            if (parent_el := sig_prop_et.find(
                f"{ns}{self.config.SIGPROP_PREMIS_SIGNIFICANT_PROPERTY_PARENT}"
            )) is not None:
                # --- Adjust indentation after manually adding elements ---
                # lxml does not automatically reindent when elements are
                # appended to an existing tree. This ensures pretty-printed
                # structure for the new elements when the tree is serialized.

                def set_indent(
                    target_el: ET._Element,
                    depth: int,
                    in_text: bool = False,
                ):
                    """
                    Set indentation for XML nodes by inserting line breaks and
                    spaces using `.text` and `.tail`.

                    Keyword arguments:
                    target_el -- target element to set indentation on
                    depth -- indentation depth
                    in_text -- If True, set the `.text` attribute.
                               Otherwise set the `.tail` attribute.
                               (default False)
                    """
                    indent = "\n" + "  " * depth
                    if in_text:
                        target_el.text = indent
                    else:
                        target_el.tail = indent

                # determine parent depth (number of ancestor levels)
                depth = len(parent_el.xpath("ancestor::*"))
                # --- Fix indentation for the opening tag ---
                if len(siblings := parent_el.getchildren()) > 0:
                    # in the tail of the last existing sibling
                    set_indent(siblings[-1], depth + 1)
                else:
                    # in the text of the parent element (no prior siblings)
                    set_indent(parent_el, depth + 1, in_text=True)
                # create and append new elements
                last_index = len(new_types) - 1
                for i, type_ in enumerate(new_types):
                    # create new element from XML string template
                    new_element_str = self.config.SIGPROP_PREMIS_SIGNIFICANT_PROPERTY_TEMPLATE.format(
                        type_=type_,
                        value=(
                            result.metadata[type_]
                            if isinstance(result.metadata[type_], str)
                            else result.metadata[type_][0]
                        ),
                    )
                    # parse string into an ET._Element
                    new_element = ET.fromstring(new_element_str)
                    # --- Fix indentation after each new element ---
                    # Use deeper indent if another element follows,
                    # otherwise apply parent-level indent.
                    set_indent(
                        new_element, depth + (0 if (i == last_index) else 1)
                    )
                    # append element
                    parent_el.append(new_element)

        # write to file
        path.write_text(
            ET.tostring(sig_prop_et, pretty_print=True).decode("utf-8"),
            encoding="utf-8",
        )

    def prepare(self, context: JobContext, info: JobInfo):
        """Job instructions for the '/prepare' endpoint."""
        os.chdir(self.config.FS_MOUNT_POINT)
        preparation_config = PreparationConfig.from_json(
            info.config.request_body["preparation"]
        )
        info.report.log.set_default_origin("Preparation Module")

        # set progress info
        info.report.progress.verbose = (
            f"preparing IP from '{preparation_config.target.path}'"
        )
        info.report.log.log(
            LoggingContext.INFO,
            body=f"Preparing IP from '{preparation_config.target.path}'.",
        )
        context.push()

        # Create path for the prepared IP or exit if not successful
        info.report.data.path = get_output_path(self.config.PREPARED_IP_OUTPUT)
        if info.report.data.path is None:
            info.report.data.success = False
            info.report.log.log(
                LoggingContext.ERROR,
                body="Unable to generate output directory in "
                + f"'{self.config.FS_MOUNT_POINT / self.config.PREPARED_IP_OUTPUT}'"
                + "(maximum retries exceeded).",
            )
            context.push()
            # make callback; rely on _run_callback to push progress-update
            info.report.progress.complete()
            self._run_callback(
                context, info, info.config.request_body.get("callback_url")
            )
            return
        info.report.log.log(
            LoggingContext.INFO,
            body=f"Preparing IP at '{info.report.data.path}'.",
        )
        context.push()

        # copy target IP to output path
        copytree(
            preparation_config.target.path,
            info.report.data.path,
            dirs_exist_ok=True,
        )
        bag = Bag(info.report.data.path)

        # create significant properties ET
        sig_prop_file = (info.report.data.path / self.config.SIGPROP_FILE_PATH)
        if sig_prop_file.is_file():
            # parse existing file
            sig_prop_et = ET.fromstring(
                sig_prop_file.read_text(encoding="utf-8")
            )
        else:
            # create empty tree from template
            sig_prop_et = ET.fromstring(self.config.SIGPROP_PREMIS_TEMPLATE)

        # prepare IP
        for stage, src_md, operations, apply in [
            (
                "bagInfoOperations",
                self.load_baginfo(bag),
                preparation_config.baginfo_operations,
                partial(self.apply_baginfo, bag),
            ),
            (
                "sigPropOperations",
                self.load_significant_properties_from_tree(
                    sig_prop_et,
                    self.config.SIGPROP_PREMIS_NAMESPACE,
                ),
                preparation_config.sig_prop_operations,
                partial(
                    self.apply_significant_properties,
                    info.report.data.path / self.config.SIGPROP_FILE_PATH,
                    sig_prop_et,
                    self.config.SIGPROP_PREMIS_NAMESPACE,
                ),
            ),
        ]:
            # continue if no operations are requested
            if len(operations) == 0:
                continue
            # process on metadata
            operator_result = self.metadata_operator.process(
                source_metadata=src_md,
                operations=operations,
            )
            info.report.log.merge(operator_result.log)
            context.push()

            # exit if preparation failed
            if LoggingContext.ERROR in info.report.log:
                info.report.data.success = False
                info.report.log.log(
                    LoggingContext.ERROR,
                    body=f"Preparing IP from '{preparation_config.target.path}'"
                    + f" failed during stage '{stage}'.",
                )
                context.push()
                # make callback; rely on _run_callback to push progress-update
                info.report.progress.complete()
                self._run_callback(
                    context, info, info.config.request_body.get("callback_url")
                )
                return

            apply(operator_result)

        # Generate new tag-manifest files
        bag.set_tag_manifests()

        # set success and log
        info.report.data.success = True
        info.report.log.log(
            LoggingContext.INFO,
            body=f"Successfully prepared IP at '{info.report.data.path}'.",
        )
        context.push()

        # make callback; rely on _run_callback to push progress-update
        info.report.progress.complete()
        self._run_callback(
            context, info, info.config.request_body.get("callback_url")
        )
