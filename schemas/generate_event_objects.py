# code to generate eEventTypes
import xml.etree.ElementTree as ET
import asyncua.ua.object_ids as obIds
import generate_model_event as gme


class EventsCodeGenerator:

    def __init__(self, event_model, output_file):
        self.output_file = output_file
        self.event_model = event_model
        self.indent = "    "
        self.iidx = 0  # indent index

    def event_list(self):
        tree = ET.parse(self.event_model)
        root = tree.getroot()
        for child in root:
            if child.tag.endswith("UAObjectType"):
                print(child.attrib)

    def write(self, line):
        if line:
            line = self.indent * self.iidx + line
        self.output_file.write(line + "\n")

    def make_header(self, events: list):
        self.write('"""')
        self.write("Autogenerated code from xml spec")
        self.write('"""')
        self.write("")
        self.write("from asyncua import ua")
        self.write("from .events import Event")
        self.write("")
        names = ", ".join(f'"{event.browseName}"' for event in events)
        self.write(f"__all__ = [{names}]")
        self.write("")

    def add_properties(self, event):
        for ref in event.references:
            if ref.referenceType == "HasProperty":
                self.write("self.add_property('{0}', {1}, {2})".format(
                    ref.refBrowseName, self.get_property_value(ref),
                    self.get_property_data_type(ref)
                ))

    def get_property_value(self, reference):
        if reference.refBrowseName == "SourceNode":
            return "sourcenode"
        elif reference.refBrowseName == "Severity":
            return "severity"
        elif reference.refBrowseName == "Status":
            return "False"
        elif reference.refBrowseName == "Message":
            return "ua.LocalizedText(message)"
        elif reference.refDataType == "NodeId":
            return "ua.NodeId(ua.ObjectIds.{0})".format(
                str(obIds.ObjectIdNames[int(str(reference.refId).split("=")[1])]).split("_")[0])
        else:
            return "None"

    def get_property_data_type(self, reference):
        if str(reference.refBrowseName).endswith("Time"):
            return "ua.VariantType.DateTime"
        elif str(reference.refDataType).startswith("i="):
            return "ua.NodeId(ua.ObjectIds.{0})".format(
                str(obIds.ObjectIdNames[int(str(reference.refDataType).split("=")[1])]).split("_")[0])
        else:
            return "ua.VariantType.{0}".format(reference.refDataType)

    def generate_event_class(self, event, *parent_event_browse_name):
        self.write("")
        if event.browseName == "BaseEvent":
            self.write("class {0}(Event):".format(event.browseName))
            self.iidx += 1
            self.write('"""')
            if event.description is not None:
                self.write(event.browseName + ": " + event.description)
            else:
                self.write(event.browseName + ": ")
            self.write('"""')
            self.write("def __init__(self, sourcenode=None, message=None, severity=1):")
            self.iidx += 1
            self.write("Event.__init__(self)")
            self.add_properties(event)
        else:
            self.write("class {0}({1}):".format(event.browseName, parent_event_browse_name[0]))
            self.iidx += 1
            self.write('"""')
            if event.description is not None:
                self.write(event.browseName + ": " + event.description)
            else:
                self.write(event.browseName + ": ")
            self.write('"""')
            self.write("def __init__(self, sourcenode=None, message=None, severity=1):")
            self.iidx += 1
            self.write("super({0}, self).__init__(sourcenode, message, severity)".format(event.browseName))
            self.write("self.EventType = ua.NodeId(ua.ObjectIds.{0}Type)".format(event.browseName))
            self.add_properties(event)
        self.iidx -= 2

    def generate_events_code(self, model):
        self.make_header(model.values())
        for event in model.values():
            if event.browseName == "BaseEvent":
                self.generate_event_class(event)
            else:
                parent_node = model[event.parentNodeId]
                self.generate_event_class(event, parent_node.browseName)
        self.write("")
        self.write("")
        self.write("IMPLEMENTED_EVENTS = {")
        self.iidx += 1
        for event in model.values():
            self.write("ua.ObjectIds.{0}Type: {0},".format(event.browseName))
        self.write("}")


if __name__ == "__main__":
    xmlPath = "Opc.Ua.NodeSet2.xml"
    output_path = "../asyncua/common/event_objects.py"
    p = gme.Parser(xmlPath)
    model = p.parse()
    with open(output_path, "w") as fp:
        ecg = EventsCodeGenerator(model, fp)
        ecg.generate_events_code(model)
