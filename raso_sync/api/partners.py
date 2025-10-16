import frappe
from werkzeug.wrappers import Response
from xml.etree.ElementTree import Element, SubElement
from raso_sync.api.sync import sync_partners_internal, format_xml_response


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def partners():
    """
    Partners (Clients) sync endpoint - DataType 1
    
    Parameters:
    - FullSync: 1 for full sync, 0 for incremental
    - recentModified: Required when FullSync=0, ISO datetime string
    
    Returns XML document directly
    """
    try:
        full_sync = int(frappe.form_dict.get("FullSync", 1))
        recent_modified = frappe.form_dict.get("recentModified")
        
        if full_sync == 0 and not recent_modified:
            frappe.throw("recentModified parameter is required when FullSync=0")
            
        root = sync_partners_internal(full_sync, recent_modified)
        
        if not list(root):
            return Response(status=204)

        return Response(format_xml_response(root), content_type='application/xml; charset=utf-8', status=200)
        
    except Exception as e:
        frappe.log_error(f"Partners sync error: {str(e)}")
        
        error_root = Element("Error")
        error_elem = SubElement(error_root, "Message")
        error_elem.text = str(e)

        return Response(
            format_xml_response(error_root),
            content_type='application/xml; charset=utf-8',
            status=500
        )