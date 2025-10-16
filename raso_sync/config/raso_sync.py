from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("RASO Sync"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "RASO Sync Log",
					"label": _("Sync Logs"),
					"description": _("View synchronization logs")
				}
			]
		}
	]