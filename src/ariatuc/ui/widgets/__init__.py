"""Reusable UI widgets."""

from ariatuc.ui.widgets.add_download_dialog import AddDownloadDialog
from ariatuc.ui.widgets.aria2_field_definitions import (
    ALL_ARIA2_FIELDS,
    ARIA2_FIELDS_ADVANCED,
    ARIA2_FIELDS_BASIC,
    ARIA2_FIELDS_BITTORRENT,
    ARIA2_FIELDS_FTP_SFTP,
    ARIA2_FIELDS_HTTP,
    ARIA2_FIELDS_HTTP_FTP_SFTP,
    ARIA2_FIELDS_METALINK,
    ARIA2_FIELDS_RPC,
)
from ariatuc.ui.widgets.command_bar import CommandBar
from ariatuc.ui.widgets.confirm_dialog import ConfirmDialog, MessageDialog
from ariatuc.ui.widgets.download_detail import DownloadDetailWidget
from ariatuc.ui.widgets.download_list import DownloadListWidget
from ariatuc.ui.widgets.field_schema import ConfigField, FieldType
from ariatuc.ui.widgets.form_widget import FormWidget
from ariatuc.ui.widgets.status_bar import StatusBar

__all__ = [
    "AddDownloadDialog",
    "ALL_ARIA2_FIELDS",
    "ARIA2_FIELDS_ADVANCED",
    "ARIA2_FIELDS_BASIC",
    "ARIA2_FIELDS_BITTORRENT",
    "ARIA2_FIELDS_FTP_SFTP",
    "ARIA2_FIELDS_HTTP",
    "ARIA2_FIELDS_HTTP_FTP_SFTP",
    "ARIA2_FIELDS_METALINK",
    "ARIA2_FIELDS_RPC",
    "CommandBar",
    "ConfigField",
    "ConfirmDialog",
    "DownloadDetailWidget",
    "DownloadListWidget",
    "FieldType",
    "FormWidget",
    "MessageDialog",
    "StatusBar",
]
