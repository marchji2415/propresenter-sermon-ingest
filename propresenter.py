import os, sys, uuid, importlib
import config
from text_utils import safe_name, clean_multiline_text, clean_single_line

pb = None

def load_pb2_from_procore(procore_dir):
    global pb
    procore_dir = os.path.abspath(procore_dir)
    if not os.path.isdir(procore_dir): raise FileNotFoundError(f"ProCore directory not found: {procore_dir}")
    if not os.path.exists(os.path.join(procore_dir, "presentation_pb2.py")): raise FileNotFoundError(f"presentation_pb2.py not found in: {procore_dir}")
    if procore_dir not in sys.path: sys.path.insert(0, procore_dir)
    pb = importlib.import_module("presentation_pb2")
    return pb

def enum_value(message, field_name, value_name):
    fd = message.DESCRIPTOR.fields_by_name[field_name]
    et = fd.enum_type
    if value_name not in et.values_by_name:
        raise KeyError(f"{value_name} invalid for {message.DESCRIPTOR.full_name}.{field_name}")
    return et.values_by_name[value_name].number

class Pro7Compiler:
    @staticmethod
    def build_presentation(slides):
        if not pb: raise RuntimeError("Protobuf module is not loaded.")
        p = pb.Presentation()
        p.uuid.string = str(uuid.uuid4()).upper()
        p.name = "Sermon Ingest"
        p.application_info.application = enum_value(p.application_info, "application", "APPLICATION_PROPRESENTER")
        p.application_info.platform = enum_value(p.application_info, "platform", "PLATFORM_WINDOWS")
        p.background.color.alpha = 1
        p.timeline.duration = 300
        p.last_modified_date.seconds = 0
        p.ccli.SetInParent()
        cue_ids = []
        for slide in slides:
            name = safe_name(slide.name)
            cue = p.cues.add()
            cue.uuid.string = str(uuid.uuid4()).upper()
            cue.name = name
            cue.isEnabled = True
            cue.completion_target_uuid.string = config.NIL_UUID
            cue.completion_action_type = enum_value(cue, "completion_action_type", "COMPLETION_ACTION_TYPE_LAST")
            cue.completion_action_uuid.string = config.NIL_UUID
            cue.trigger_time.SetInParent()
            cue_ids.append(cue.uuid.string)
            action = cue.actions.add()
            action.uuid.string = str(uuid.uuid4()).upper()
            action.label.text = name
            action.isEnabled = True
            action.type = enum_value(action, "type", "ACTION_TYPE_PRESENTATION_SLIDE")
            base = action.slide.presentation.base_slide
            base.uuid.string = str(uuid.uuid4()).upper()
            base.size.width = config.CANVAS_WIDTH
            base.size.height = config.CANVAS_HEIGHT
            base.background_color.alpha = 1
            if slide.kind == "title":
                Pro7Compiler._add_text_element(base, slide.body, config.TITLE_X, config.TITLE_Y, config.TITLE_W, config.TITLE_H, config.IS_TITLE_BOLD, config.TITLE_FONT_SIZE, name, font_name=config.FONT_NAME, font_family=config.FONT_FAMILY, font_face=config.FONT_FACE, margin_left=0, margin_right=0)
            elif slide.kind == "point":
                label = f"POINT {slide.point_number or 1}"
                Pro7Compiler._add_text_element(base, label, config.POINT_NUMBER_X, config.POINT_NUMBER_Y, config.POINT_NUMBER_W, config.POINT_NUMBER_H, config.IS_POINT_LABEL_BOLD, config.POINT_NUMBER_FONT_SIZE, label, font_name=config.FONT_NAME, font_family=config.FONT_FAMILY, font_face=config.FONT_FACE, margin_left=0, margin_right=0)
                Pro7Compiler._add_text_element(base, slide.body, config.POINT_CONTENT_X, config.POINT_CONTENT_Y, config.POINT_CONTENT_W, config.POINT_CONTENT_H, config.IS_POINT_BODY_BOLD, config.POINT_CONTENT_FONT_SIZE, name, font_name=config.FONT_NAME, font_family=config.FONT_FAMILY, font_face=config.FONT_FACE, margin_left=config.MARGIN_LEFT, margin_right=config.MARGIN_RIGHT)
            else:
                Pro7Compiler._add_text_element(base, slide.body, config.BODY_X, config.BODY_Y, config.BODY_W, config.BODY_H, config.IS_BODY_BOLD, config.BODY_FONT_SIZE, safe_name(slide.body), font_name=config.FONT_NAME, font_family=config.FONT_FAMILY, font_face=config.FONT_FACE, margin_left=config.MARGIN_LEFT, margin_right=config.MARGIN_RIGHT)
                if slide.label and slide.label.strip():
                    Pro7Compiler._add_text_element(base, slide.label, config.LABEL_X, config.LABEL_Y, config.LABEL_W, config.LABEL_H, config.IS_LABEL_BOLD, config.LABEL_FONT_SIZE, name, font_name=config.FONT_NAME, font_family=config.FONT_FAMILY, font_face=config.FONT_FACE, margin_left=0, margin_right=0)
            action.slide.presentation.notes.SetInParent()
            action.slide.presentation.chord_chart.SetInParent()
        group = p.cue_groups.add()
        group.group.uuid.string = str(uuid.uuid4()).upper()
        group.group.name = "SERMON"
        group.group.application_group_identifier.string = group.group.uuid.string
        group.group.application_group_name = "SERMON"
        for cid in cue_ids: group.cue_identifiers.add().string = cid
        arr = p.arrangements.add()
        arr.uuid.string = str(uuid.uuid4()).upper()
        arr.name = "Default Arrangement"
        arr.group_identifiers.add().string = group.group.uuid.string
        p.selected_arrangement.string = arr.uuid.string
        return p

    @staticmethod
    def _add_text_element(base_slide, text_payload, x, y, w, h, is_bold, font_size, element_name=None, font_name="Arial", font_family="Arial", font_face="Regular", margin_left=None, margin_right=None):
        text_payload = clean_single_line(text_payload)
        if margin_left is None:
            margin_left = getattr(config, "MARGIN_LEFT", 0)
        if margin_right is None:
            margin_right = getattr(config, "MARGIN_RIGHT", 0)
        wrapper = base_slide.elements.add()
        element = wrapper.element
        element.uuid.string = str(uuid.uuid4()).upper()
        element.name = safe_name(clean_single_line(element_name or text_payload))
        element.bounds.origin.x = x; element.bounds.origin.y = y
        element.bounds.size.width = w; element.bounds.size.height = h
        element.opacity = 1.0
        element.path.closed = True
        for px, py in [(0,0),(1,0),(1,1),(0,1)]:
            pt = element.path.points.add()
            pt.point.x=px; pt.point.y=py; pt.q0.x=px; pt.q0.y=py; pt.q1.x=px; pt.q1.y=py
        element.path.shape.type = enum_value(element.path.shape, "type", "TYPE_RECTANGLE")
        element.fill.color.alpha = 0.0
        element.text.vertical_alignment = enum_value(element.text, "vertical_alignment", "VERTICAL_ALIGNMENT_MIDDLE")
        element.text.rtf_data = Pro7Compiler._build_rtf(text_payload, is_bold, font_size, font_name).encode("ascii", errors="replace")
        attrs = element.text.attributes
        attrs.font.name = font_name; attrs.font.family = font_family; attrs.font.face = font_face; attrs.font.size = font_size; attrs.font.bold = is_bold
        attrs.text_solid_fill.red=1; attrs.text_solid_fill.green=1; attrs.text_solid_fill.blue=1; attrs.text_solid_fill.alpha=1
        attrs.paragraph_style.alignment = enum_value(attrs.paragraph_style, "alignment", "ALIGNMENT_CENTER")
        attrs.paragraph_style.line_height_multiple = 1
        attrs.paragraph_style.text_list.SetInParent()
        element.text.margins.left = margin_left; element.text.margins.right = margin_right
        element.text_line_mask.SetInParent()
        wrapper.info = 3
        wrapper.text_scroller.scroll_rate = 0.5
        wrapper.text_scroller.should_repeat = True
        wrapper.text_scroller.repeat_distance = 0.0625

    @staticmethod
    def _escape_rtf_text(text):
        text = clean_multiline_text(text)
        text = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
        # Insert a space before the RTF \line command to prevent word gluing
        # when text is edited or copied in ProPresenter.
        text = text.replace("\n", " \\line ")
        return text

    @staticmethod
    def _build_rtf(text_payload, is_bold, font_size, font_name="Arial"):
        escaped = Pro7Compiler._escape_rtf_text(text_payload)
        bold = "\\b" if is_bold else "\\b0"
        return ("{\\rtf1\\ansi\\ansicpg1252"
                f"{{\\fonttbl{{\\f0\\fnil {font_name};}}}}"
                "{\\colortbl;\\red255\\green255\\blue255;}"
                "\\viewkind4\\uc1\\kerning0\\expnd0\\expndtw0"
                f"\\pard\\qc\\f0{bold}\\fs{font_size*2}\\cf1 "
                f"{escaped}"
                + ("\\b0" if is_bold else "")
                + "}")
