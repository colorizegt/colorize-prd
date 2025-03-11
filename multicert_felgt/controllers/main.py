# -*- coding: utf-8 -*-

import json
import logging

from werkzeug.urls import url_decode

from odoo.http import (
    content_disposition,
    request
)
from odoo.tools import html_escape
from odoo import http
import werkzeug.exceptions

import odoo.addons.web.controllers.report as report

_logger = logging.getLogger(__name__)


class ReportController(report.ReportController):

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == "g4s_pdf":
            report = request.env["ir.actions.report"]._get_report_from_converter(converter)
            context = dict(request.env.context)
            if docids:
                docids = [int(i) for i in docids.split(",")]
            if data.get("options"):
                final_data = json.loads(data.get("options"))
                final_data = json.loads(final_data)
            if data.get("context"):
                
                data["context"] = json.loads(data["context"])
            g4s_pdf = report.with_context(**context)._render_g4s_pdf(docids)
            httpheaders = [
                ("Content-Type","application/pdf"),
                ("Content-Length", len(g4s_pdf)),
            ]
            return request.make_response(g4s_pdf, headers=httpheaders)
        return super(ReportController, self).report_routes(reportname, docids, converter, **data)

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, context=None, token=None):
        """This function is used by 'action_manager_report.js' in order to trigger the download of
        a pdf/controller report.

        :param data: a javascript array JSON.stringified containg report internal url ([0]) and
        type [1]
        :returns: Response with an attachment header

        """
        requestcontent = json.loads(data)
        url, type_ = requestcontent[0], requestcontent[1]
        reportname = '???'
        try:
            if type_ == "g4s_pdf":
                reportname = url.split("/report/g4s_pdf/")[1].split("?")[0]
                docids = None
                if "/" in reportname:
                    reportname, docids = reportname.split("/")
                if docids:
                    # Generic report:
                    response = self.report_routes(
                        reportname, docids=docids, converter="g4s_pdf", context=context
                    )
                else:
                    # Particular report:
                    data = dict(
                        url_decode(url.split("?")[1]).items()
                    )  # decoding the args represented in JSON
                    if "context" in data:
                        context, data_context = json.loads(context or "{}"), json.loads(
                            data.pop("context")
                        )
                        context = json.dumps({**context, **data_context})
                    response = self.report_routes(
                        reportname, converter="g4s_pdf", context=context, **data
                    )

                filename = "%s.%s" % ('DTE', "pdf")

                if docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env['account.move'].browse(ids)

                    if obj:
                        report_name = "DTE-" + str(obj.dte_number)
                        filename = "%s.%s" % (report_name, "pdf")
                response.headers.add(
                    "Content-Disposition", content_disposition(filename)
                )
                return response
            else:
                return super(ReportController, self).report_download(data, context)
            
        except Exception as e:
            _logger.warning("Error while generating report %s", reportname, exc_info=True)
            se = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            res = request.make_response(html_escape(json.dumps(error)))
            raise werkzeug.exceptions.InternalServerError(response=res) from e