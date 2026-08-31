
def parse_element(element):
    info = element.element_info
    return {
        "name": info.name,
        "automation_id": info.automation_id,
        "control_type": info.control_type,
        "class_name": info.class_name,
        "rectangle": str(info.rectangle)
    }