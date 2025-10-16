import frappe
from werkzeug.wrappers import Response
from xml.etree.ElementTree import Element, SubElement, tostring
from datetime import datetime
import re


def sync_partners_internal(full_sync, recent_modified):
    """Internal function for Partners sync"""
    # Build filters
    filters = {"disabled": 0}  # Only enabled customers
    
    if full_sync == 0 and recent_modified:
        modified_date = datetime.fromisoformat(recent_modified)
        filters["modified"] = (">", modified_date)
    
    # Fetch customers
    customers = frappe.get_all(
        "Customer",
        filters=filters,
        fields=["business_code", "customer_name", "tax_id", "customer_primary_address", "disabled", "modified"]
    )
    root = Element("PartnersSync")
    root.set("FullSync", str(full_sync))
    
    for customer in customers:
        if not customer.get("customer_name") or customer.get("business_code") is None:
            continue # Code here is used as unique identifier, skip if missing
        
        partner_elem = SubElement(root, "Partners")
        
        code_elem = SubElement(partner_elem, "Code")
        code_elem.text = customer.get("business_code", "") # Using custom field 'business_code' as Code
        
        name_elem = SubElement(partner_elem, "Name")
        name_elem.text = customer.get("customer_name", "")
        
        vat_elem = SubElement(partner_elem, "VATCode")
        vat_elem.text = customer.get("tax_id", "")
        
        address_text = ""
        if customer.get("customer_primary_address"):
            try:
                address_doc = frappe.get_doc("Address", customer.get("customer_primary_address"))
                address_parts = []
                if address_doc.address_line1:
                    address_parts.append(address_doc.address_line1)
                if address_doc.address_line2:
                    address_parts.append(address_doc.address_line2)
                if address_doc.city:
                    address_parts.append(address_doc.city)
                if address_doc.country:
                    address_parts.append(address_doc.country)
                address_text = ", ".join(address_parts)
            except:
                address_text = ""
        
        address_elem = SubElement(partner_elem, "Address")
        address_elem.text = address_text
        
        enabled_elem = SubElement(partner_elem, "Enabled")
        enabled_elem.text = "0" if customer.get("disabled") else "1"
    
    return root


def sync_goods_groups_internal(full_sync, last_update):
    """Internal function for GoodsGroups sync"""
    filters = {}
    if full_sync == 0 and last_update:
        modified_date = datetime.fromisoformat(last_update)
        filters["modified"] = (">", modified_date)

    # item_groups = frappe.get_all(
    #     "Item Group",
    #     filters=filters,
    #     fields=["name", "item_group_name", "is_visible_in_catalog", "modified"]
    # )
    
    item_groups = frappe.db.sql("""
        SELECT CRC32(ig.name) AS id, ig.name, ig.item_group_name, ig.is_visible_in_catalog, ig.modified
        FROM `tabItem Group` ig
        LEFT JOIN `tabItem Group` parent ON ig.parent_item_group = parent.name
        WHERE (parent.name = 'Prekės' OR parent.parent_item_group = 'Prekės')
        AND ig.is_visible_in_catalog = 0
        {filters_clause}
    """.format(
        filters_clause="AND ig.modified > '{modified}'".format(modified=filters["modified"][1].strftime("%Y-%m-%d %H:%M:%S")) if "modified" in filters else ""
    ), filters, as_dict=1)
    
    root = Element("GoodsGroupsSync")
    root.set("FullSync", str(full_sync))
    
    for item_group in item_groups:
        group_elem = SubElement(root, "GoodsGroups")
        
        code_elem = SubElement(group_elem, "Code")
        code_elem.text = item_group.get("id", "") # TODO: not ideal, check if hash can be used
        
        name_elem = SubElement(group_elem, "Name")
        name_elem.text = item_group.get("item_group_name", "")
        
        refundable_elem = SubElement(group_elem, "Refundable")
        refundable_elem.text = "1"
        
        enabled_elem = SubElement(group_elem, "Enabled")
        enabled_elem.text = "1" if item_group.get("is_visible_in_catalog") else "0"
        
        edit_date_elem = SubElement(group_elem, "EditDate")
        if item_group.get("modified"):
            modified_dt = item_group.get("modified")
            if isinstance(modified_dt, str):
                modified_dt = datetime.fromisoformat(modified_dt)
            edit_date_elem.text = modified_dt.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            edit_date_elem.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    return root


def sync_goods_internal(full_sync, recent_modified):
    """Internal function for Goods sync"""
    filters = {}
    if full_sync == 0 and recent_modified:
        modified_date = datetime.fromisoformat(recent_modified)
        filters["modified"] = (">", modified_date)
    
    items = frappe.get_all(
        "Item",
        filters=filters,
        fields=["name", "item_code", "item_name", "item_group", "stock_uom", "description", "disabled", "modified", "deposit_package_count"],
        limit_page_length=200
    )
    
    root = Element("GoodsSync")
    root.set("FullSync", str(full_sync))
    
    for item in items:
        if not item.get("item_code") and not item.get("name"):
            continue
        # barcode is mandatory
        barcode = frappe.db.get_value("Item Barcode", {"parent": item.get("name")}, "barcode")
        if not barcode:
            continue
        
        # check if the item has an Item Price, if not, skip it
        price_exists = frappe.db.exists("Item Price", {"item_code": item.get("item_code"), "selling": 1})
        if not price_exists:
            continue
        
        if item.get("disabled") and full_sync == 1:
            continue

        goods_elem = SubElement(root, "Goods")
        
        code_elem = SubElement(goods_elem, "Code")
        code_elem.text = barcode
        
        vcode_elem = SubElement(goods_elem, "VCode")
        vcode_elem.text = item.get("item_code", barcode)
        
        name_elem = SubElement(goods_elem, "Name")
        # requires truncation to 80 characters for RASO compatibility
        item_name = item.get("item_name", "") or item.get("item_code", "")
        if len(item_name) > 80:
            item_name = item_name[:80]
        name_elem.text = item_name

        vat_code_elem = SubElement(goods_elem, "VatCode")
        vat_code_elem.text = "3" if barcode == 1100 else "1"
        # TODO: Implement proper field or use tax templates to select VAT code
        # 1 stand for A (21%) in the fiscal module, and so on.
        # So far only, a single item which is 0% VAT
        
        unit_elem = SubElement(goods_elem, "Unit")
        unit_elem.text = item.get("stock_uom", "")
        
        extra_info_elem = SubElement(goods_elem, "ExtraInfo")
        refundable_elem = SubElement(goods_elem, "Refundable")

        item_group = item.get("item_group")
        if item_group:
            # Fetch item group information
            item_group_info = frappe.db.sql("""
            SELECT CRC32(ig.name) AS crc32, ig.pos_department_no AS dep_no, ig.is_refundable AS is_refundable
            FROM `tabItem Group` ig WHERE ig.name = %s
            """, (item_group,), as_dict=True)

            if item_group_info:
                item_group_info = item_group_info[0]
                extra_info_elem.text = str(item_group_info.get("crc32", ""))
                refundable_elem.text = "1" if item_group_info.get("is_refundable") else "0"
                if item_group_info.get("dep_no") and item_group_info.get("dep_no") != 0:
                    dep_no_elem = SubElement(goods_elem, "DepNo")
                    dep_no_elem.text = str(item_group_info.get("dep_no", 1))
            else:
                extra_info_elem.text = ""
                refundable_elem.text = "0"
        else:
            extra_info_elem.text = ""
            refundable_elem.text = "0"
        

        if  item.get("deposit_package_count") and item.get("deposit_package_count") > 0:
            extra_qty_elem = SubElement(goods_elem, "ExtraQty")
            extra_qty_elem.text = str(item.get("deposit_package_count", 1)) #+ ".000000"
            extra_code_elem = SubElement(goods_elem, "ExtraCode")
            extra_code_elem.text = "1100"  # 1100 is the barcode for deposit packages
            
            
            
        if item.get("description"):
            text_elem = SubElement(goods_elem, "Text")
            text_elem.text = item.get("description", "")
        
        
        comment_required_elem = SubElement(goods_elem, "CommentRequired")
        comment_required_elem.text = "0"
        
        is_weighing_elem = SubElement(goods_elem, "IsWeighing")
        is_weighing_elem.text = '1' if item.get("stock_uom") == "Kg" or item.get("stock_uom") == "kg" else '0'
        
        enabled_elem = SubElement(goods_elem, "Enabled")
        enabled_elem.text = "0" if item.get("disabled") else "1"
        
        change_price_elem = SubElement(goods_elem, "ChangePriceManually")
        change_price_elem.text = "0"
        
        edit_date_elem = SubElement(goods_elem, "EditDate")
        if item.get("modified"):
            modified_dt = item.get("modified")
            if isinstance(modified_dt, str):
                modified_dt = datetime.fromisoformat(modified_dt)
            edit_date_elem.text = modified_dt.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            edit_date_elem.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    return root


def sync_goods_prices_internal(full_sync, recent_modified):
    """Internal function for GoodsPrices sync"""
    filters = {}
    if full_sync == 0 and recent_modified:
        modified_date = datetime.fromisoformat(recent_modified)
        filters["modified"] = (">", modified_date)
    
    item_prices = frappe.get_all(
        "Item Price",
        filters=filters,
        fields=["name", "item_code", "price_list", "price_list_rate", "packing_unit", "modified", "valid_from", "selling", "valid_upto"]
    )
    
    root = Element("GoodsPricesSync")
    root.set("FullSync", str(full_sync))
    
    for item_price in item_prices:
        barcode = frappe.db.get_value("Item Barcode", {"parent": item_price.get("item_code")}, "barcode")
        # TODO: use a single SQL query to join the tables
        price_elem = SubElement(root, "GoodsPrices")
        
        goods_code_elem = SubElement(price_elem, "GoodsCode")
        goods_code_elem.text = barcode
        
        shop_no_elem = SubElement(price_elem, "ShopNo")
        shop_no_elem.text = "01"
        
        # TODO: add DateFrom and DateTo
        
        qty_elem = SubElement(price_elem, "Qty")
        qty_elem.text = str(item_price.get("packing_unit", 0))
        
        price_elem_inner = SubElement(price_elem, "Price")
        price_elem_inner.text = str(item_price.get("price_list_rate", 0.0))
        
        enabled_elem = SubElement(price_elem, "Enabled")
        enabled_elem.text = "1"
        
        change_price_elem = SubElement(price_elem, "ChangePriceManually")
        change_price_elem.text = "0"
        
        edit_date_elem = SubElement(price_elem, "EditDate")
        if item_price.get("modified"):
            modified_dt = item_price.get("modified")
            if isinstance(modified_dt, str):
                modified_dt = datetime.fromisoformat(modified_dt)
            edit_date_elem.text = modified_dt.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            edit_date_elem.text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    return root


def format_xml_response(root):
    """Format XML with proper declaration and pretty printing"""
    # Ensure all text values in the XML are strings
    for elem in root.iter():
        if elem.text is not None and not isinstance(elem.text, str):
            elem.text = str(elem.text)
            
    return '<?xml version="1.0" encoding="UTF-8"?>' + tostring(root, encoding='unicode')


@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def sync():
    """
    Main API endpoint for RASO sync data - Returns XML directly
    
    Parameters:
    - DataType: 1 (Partners), 2 (GoodsGroups), 3 (Goods), 4 (GoodsPrices)
    - FullSync: 1 for full sync, 0 for incremental
    - recentModified: Required when FullSync=0, ISO datetime string
    
    Returns XML document directly
    """
    try:
        # Get parameters
        data_type = frappe.form_dict.get("DataType")
        full_sync = int(frappe.form_dict.get("FullSync", 1))
        recent_modified = frappe.form_dict.get("recentModified")
        
        # Validate parameters
        if not data_type:
            frappe.throw("DataType parameter is required")
        
        if full_sync == 0 and not recent_modified:
            frappe.throw("recentModified parameter is required when FullSync=0")
        
        # Route to appropriate sync function
        if data_type == "1":
            root = sync_partners_internal(full_sync, recent_modified)
        elif data_type == "2":
            root = sync_goods_groups_internal(full_sync, recent_modified)
        elif data_type == "3":
            root = sync_goods_internal(full_sync, recent_modified)
        elif data_type == "4":
            root = sync_goods_prices_internal(full_sync, recent_modified)
        else:
            frappe.throw(f"Invalid DataType '{data_type}'. Supported values: 1 (Partners), 2 (GoodsGroups), 3 (Goods), 4 (GoodsPrices)")
        
        return Response(
            format_xml_response(root),
            content_type='application/xml; charset=utf-8',
            status=200
        )
            
    except Exception as e:
        frappe.log_error(f"RASO sync API error: {str(e)}")
        
        # Return error as XML
        error_root = Element("Error")
        error_elem = SubElement(error_root, "Message")
        error_elem.text = str(e)
        
        return Response(
            format_xml_response(error_root),
            content_type='application/xml; charset=utf-8',
            status=500
        )