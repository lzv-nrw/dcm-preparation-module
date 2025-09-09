"""
Preparation View-class definition
"""

from typing import Optional
from shutil import copytree
from pathlib import Path
from xml.etree import ElementTree
from functools import partial
import os
from uuid import uuid4

from bagit import Bag
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
        return bag.info

    def apply_baginfo(self, bag: Bag, result: ProcessResult) -> dict:
        """
        Updates contents of `bag.info`.
        """
        bag.info = result.metadata

    @staticmethod
    def load_significant_properties(path: Path, ns: str) -> dict:
        """
        Returns existing 'significant_properties.xml'-metadata as dictionary or
        an empty dict if not existing.
        """
        # check conditions
        if not path.is_file():
            return {}

        # parse
        et = ElementTree.fromstring(path.read_text(encoding="utf-8"))
        try:
            significant_properties = et.find(f"{ns}object").findall(
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
        self, path: Path, result: ProcessResult
    ) -> dict:
        """
        Updates contents of 'significant_properties.xml'.
        """
        # check conditions
        if not result.metadata:
            return

        # write to file
        path.write_text(
            self.config.SIGPROP_PREMIS_TEMPLATE.format(
                "".join(
                    [
                        self.config.SIGPROP_PREMIS_SIGNIFICANT_PROPERTY_TEMPLATE.format(
                            type_=type_,
                            value=(
                                result.metadata[type_]
                                if isinstance(result.metadata[type_], str)
                                else result.metadata[type_][0]
                            ),
                        )
                        for type_ in self.config.SIGPROP_TYPES
                        if type_ in result.metadata
                    ]
                )
            ),
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
        bag = Bag(str(info.report.data.path))

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
                self.load_significant_properties(
                    info.report.data.path / self.config.SIGPROP_FILE_PATH,
                    self.config.SIGPROP_PREMIS_NAMESPACE,
                ),
                preparation_config.sig_prop_operations,
                partial(
                    self.apply_significant_properties,
                    info.report.data.path / self.config.SIGPROP_FILE_PATH,
                ),
            ),
        ]:
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
        # (manifests=False -> manifest files do not have to be updated)
        bag.save(processes=1, manifests=False)

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
