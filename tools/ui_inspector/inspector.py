"""
UI Inspector utility for analyzing Qt-based UI structures.
This tool provides detailed information about widget hierarchies, properties, and layouts.
"""

from PyQt6.QtWidgets import QWidget, QLayout, QGridLayout
from PyQt6.QtCore import QObject, QMetaMethod
from PyQt6.QtCore import Qt
import json
from typing import Dict, Any, Optional, List, Tuple
import logging

class UIInspector:
    """A utility class for inspecting and analyzing Qt UI widget hierarchies."""
    
    def __init__(self, root_widget: QWidget):
        self.root_widget = root_widget
        self.widget_info = {}
        
    def inspect(self) -> Dict[str, Any]:
        """Inspect the entire widget hierarchy starting from the root widget."""
        return self._inspect_widget(self.root_widget)
    
    def _inspect_widget(self, widget: QWidget, parent_path: str = "") -> Dict[str, Any]:
        """Recursively inspect a widget and its children."""
        if not widget:
            return {}
            
        # Get basic widget info
        widget_name = widget.objectName() or widget.__class__.__name__
        current_path = f"{parent_path}/{widget_name}" if parent_path else widget_name
        
        info = {
            "class": widget.__class__.__name__,
            "objectName": widget.objectName(),
            "geometry": {
                "x": widget.x(),
                "y": widget.y(),
                "width": widget.width(),
                "height": widget.height()
            },
            "visible": widget.isVisible(),
            "enabled": widget.isEnabled(),
            "path": current_path,
            "properties": self._get_widget_properties(widget),
            "eventConnections": self._get_event_connections(widget),
            "accessibility": self._get_accessibility_info(widget),
            "state": self._get_widget_state(widget),
            "tabOrder": self._get_tab_order_info(widget),
            "children": []
        }
        
        # Inspect layout if exists
        if widget.layout():
            info["layout"] = self._inspect_layout(widget.layout())
            
        # Recursively inspect child widgets
        for child in widget.findChildren(QWidget, "", Qt.FindChildOption.FindDirectChildrenOnly):
            child_info = self._inspect_widget(child, current_path)
            if child_info:
                info["children"].append(child_info)
                
        return info

    def _get_event_connections(self, widget: QWidget) -> List[Dict[str, str]]:
        """Extract information about signal connections."""
        connections = []
        try:
            for i in range(widget.metaObject().methodCount()):
                method = widget.metaObject().method(i)
                if method.methodType() == QMetaMethod.MethodType.Signal:
                    signal_name = bytes(method.name()).decode()
                    connections.append({
                        "signal": signal_name,
                        "signature": bytes(method.methodSignature()).decode()
                    })
        except Exception as e:
            logging.warning(f"Error getting event connections for {widget}: {str(e)}")
        return connections
        
    def _get_accessibility_info(self, widget: QWidget) -> Dict[str, Any]:
        """Extract accessibility-related properties."""
        info = {
            "accessibleName": widget.accessibleName(),
            "accessibleDescription": widget.accessibleDescription(),
        }
        return info

    def _get_widget_state(self, widget: QWidget) -> Dict[str, Any]:
        """Extract current widget state information."""
        state = {
            "hasFocus": widget.hasFocus(),
            "isActiveWindow": widget.isActiveWindow(),
            "isEnabled": widget.isEnabled(),
            "isVisible": widget.isVisible(),
            "isModal": widget.isModal() if hasattr(widget, 'isModal') else False,
        }
        
        # Add widget-specific state information
        try:
            if hasattr(widget, 'isChecked'):
                state["isChecked"] = widget.isChecked()
            if hasattr(widget, 'currentText'):
                state["currentText"] = widget.currentText()
            if hasattr(widget, 'value'):
                state["value"] = widget.value()
        except Exception as e:
            logging.warning(f"Error getting widget state for {widget}: {str(e)}")
        return state

    def _get_tab_order_info(self, widget: QWidget) -> Dict[str, Any]:
        """Extract tab order information."""
        return {
            "tabIndex": widget.focusPolicy() != Qt.FocusPolicy.NoFocus,
            "nextInTabOrder": widget.nextInFocusChain().objectName() if widget.nextInFocusChain() else None,
            "previousInTabOrder": widget.previousInFocusChain().objectName() if widget.previousInFocusChain() else None
        }
    
    def _inspect_layout(self, layout: QLayout) -> Dict[str, Any]:
        """Inspect a layout's properties."""
        info = {
            "class": layout.__class__.__name__,
            "spacing": layout.spacing(),
            "margins": {
                "left": layout.contentsMargins().left(),
                "top": layout.contentsMargins().top(),
                "right": layout.contentsMargins().right(),
                "bottom": layout.contentsMargins().bottom()
            },
            "item_count": layout.count()
        }
        
        # Add grid-specific information for QGridLayout
        if isinstance(layout, QGridLayout):
            info["grid"] = self._inspect_grid_layout(layout)
            
        return info
        
    def _inspect_grid_layout(self, layout: QGridLayout) -> Dict[str, Any]:
        """Extract grid layout specific information."""
        grid_info = {
            "rowCount": layout.rowCount(),
            "columnCount": layout.columnCount(),
            "items": []
        }
        
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget():
                pos = layout.getItemPosition(i)
                grid_info["items"].append({
                    "widget": item.widget().objectName() or item.widget().__class__.__name__,
                    "row": pos[0],
                    "column": pos[1],
                    "rowSpan": pos[2],
                    "columnSpan": pos[3]
                })
                
        return grid_info
    
    def _get_widget_properties(self, widget: QWidget) -> Dict[str, Any]:
        """Extract relevant properties from a widget."""
        properties = {}
        
        # Common properties for all widgets
        try:
            if hasattr(widget, "text"):
                properties["text"] = widget.text() if callable(widget.text) else str(widget.text)
            if hasattr(widget, "placeholderText"):
                properties["placeholder"] = widget.placeholderText()
            if hasattr(widget, "toolTip"):
                properties["tooltip"] = widget.toolTip()
            if hasattr(widget, "styleSheet"):
                properties["stylesheet"] = widget.styleSheet()
            if hasattr(widget, "minimumSize"):
                properties["minimumSize"] = {
                    "width": widget.minimumWidth(),
                    "height": widget.minimumHeight()
                }
            if hasattr(widget, "maximumSize"):
                properties["maximumSize"] = {
                    "width": widget.maximumWidth(),
                    "height": widget.maximumHeight()
                }
            if hasattr(widget, "sizePolicy"):
                policy = widget.sizePolicy()
                properties["sizePolicy"] = {
                    "horizontal": str(policy.horizontalPolicy()),
                    "vertical": str(policy.verticalPolicy()),
                    "horizontalStretch": policy.horizontalStretch(),
                    "verticalStretch": policy.verticalStretch()
                }
        except Exception as e:
            logging.warning(f"Error getting properties for widget {widget}: {str(e)}")
            
        return properties
    
    def generate_report(self, output_file: Optional[str] = None, format: str = "text") -> str:
        """Generate a human-readable report of the UI structure.
        
        Args:
            output_file: Optional path to save the report
            format: Output format - "text" or "json"
        """
        ui_data = self.inspect()
        
        if format == "json":
            report = json.dumps(ui_data, indent=2)
        else:
            report = self._generate_report_section(ui_data)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
                
        return report
    
    def _generate_report_section(self, data: Dict[str, Any], level: int = 0) -> str:
        """Recursively generate a section of the report."""
        indent = "  " * level
        lines = []
        
        # Widget header
        lines.append(f"{indent}Widget: {data['class']} ({data['objectName'] or 'unnamed'})")
        lines.append(f"{indent}Path: {data['path']}")
        
        # Geometry
        geo = data['geometry']
        lines.append(f"{indent}Position: ({geo['x']}, {geo['y']}) Size: {geo['width']}x{geo['height']}")
        
        # State
        state = data.get('state', {})
        state_str = ", ".join(f"{k}={v}" for k, v in state.items() if v is not None)
        if state_str:
            lines.append(f"{indent}State: {state_str}")
        
        # Properties
        props = data.get('properties', {})
        if props:
            lines.append(f"{indent}Properties:")
            for k, v in props.items():
                if isinstance(v, dict):
                    lines.append(f"{indent}  {k}:")
                    for sub_k, sub_v in v.items():
                        lines.append(f"{indent}    {sub_k}: {sub_v}")
                else:
                    lines.append(f"{indent}  {k}: {v}")
        
        # Layout
        if 'layout' in data:
            layout = data['layout']
            lines.append(f"{indent}Layout: {layout['class']}")
            if 'grid' in layout:
                grid = layout['grid']
                lines.append(f"{indent}  Grid: {grid['rowCount']}x{grid['columnCount']}")
                for item in grid['items']:
                    lines.append(f"{indent}  - {item['widget']} at ({item['row']}, {item['column']}) "
                               f"span ({item['rowSpan']}, {item['columnSpan']})")
        
        # Children
        if data['children']:
            lines.append(f"{indent}Children:")
            for child in data['children']:
                lines.append(self._generate_report_section(child, level + 1))
        
        return "\n".join(lines)
