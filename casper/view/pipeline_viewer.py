#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from pprint import pprint
import weakref
import operator

# Qt import
from PySide import QtCore, QtGui

# Casper import
from casper.pipeline import Pbox
from casper.pipeline import Ibox
from casper.pipeline import Bbox
from casper.pipeline.utils import ControlObject
from .colors import *


class Control(QtGui.QGraphicsPolygonItem):
    """ Create a glyph for each control connection.
    """

    def __init__(self, control, name, height, width, optional, parent=None):
        """ Initilaize the Control class.

        Parameters
        ----------
        control: casper.lib.controls (mandatory)
            the control to draw.
        name: str (mandatory)
            the control name.
        height, width: int (mandatory)
            the control size.
        optional: bool (mandatory)
            option to color the glyph.
        """
        # Inheritance
        super(Control, self).__init__(parent)

        # Class parameters
        self.name = name
        self.control = control
        self.optional = optional
        color = self._color(optional)
        self.brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
        self.brush.setColor(color)

        # Set graphic item properties
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton)

        # Define the widget
        polygon = QtGui.QPolygonF([
            QtCore.QPointF(0, 0), QtCore.QPointF(width, (height - 5) / 2.0),
            QtCore.QPointF(0, height - 5)])
        self.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.setPolygon(polygon)
        self.setBrush(self.brush)
        self.setZValue(3)

    def _color(self, optional):
        """ Define the color of a control glyph depending on its status.

        Parameters
        ----------
        optional: bool (mandatory)
            option to color the glyph.

        Returns
        -------
        color: QColor
            the glyph color.
        """
        if optional:
            color = QtCore.Qt.darkGreen
        else:
            color = QtCore.Qt.black
        return color

    def get_control_point(self):
        """ Give the relative location of the control glyph in the parent
        widget.

        Returns
        -------
        position: QPointF
            the control glyph position.
        """
        point = QtCore.QPointF(
            self.boundingRect().size().width() / 2.0,
            self.boundingRect().size().height() / 2.0)
        return self.mapToParent(point)


class Node(QtGui.QGraphicsItem):
    """ A box node.
    """
    _colors = {
        "default": (RED_1, RED_2, LIGHT_RED_1, LIGHT_RED_2),
        "pbox": (SAND_1, SAND_2, LIGHT_SAND_1, LIGHT_SAND_2),
        "bbox": (DEEP_PURPLE_1, DEEP_PURPLE_2, PURPLE_1, PURPLE_2),
        "ibox": (BLUE_1, BLUE_2, LIGHT_BLUE_1, LIGHT_BLUE_2)
    }

    def __init__(self, name, inputs, outputs, active=True, style=None,
                 parent=None, pbox=None):
        """ Initilaize the Node class.

        Parameters
        ----------
        name: string (mandatory)
            a name for the box node.
        inputs: ControlObject (mandatory)
            the box input controls. If None no input will be created.
        outputs: ControlObject (mandatory)
            the box output controls. If None no output will be created.
        active: bool (optional, default True)
            a special color will be applied on the node rendering depending
            of this parameter.
        style: string (optional, default None)
            the style that will be applied to tune the box rendering.
        pbox: casper.pipeline.Pbox (optional, default None)
            the pipeline contained in the created box node.
        """
        # Inheritance
        super(Node, self).__init__(parent)

        # Class parameters
        self.style = style or "default"
        self.name = name
        self.inputs = inputs or ControlObject()
        self.outputs = outputs or ControlObject()
        self.input_names = self.inputs.controls
        self.output_names = self.outputs.controls
        self.active = active
        self.pbox = pbox
        self.input_controls = {}
        self.output_controls = {}
        self.embedded_pbox = None

        # Set graphic item properties
        self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        self.setAcceptedMouseButtons(
            QtCore.Qt.LeftButton | QtCore.Qt.RightButton |
            QtCore.Qt.MiddleButton)

        # Define rendering colors
        bgd_color_indices = [2, 3]
        if self.active:
            bgd_color_indices = [0, 1]
        self.background_brush = self._get_brush(
            *operator.itemgetter(*bgd_color_indices)(self._colors[self.style]))
        self.title_brush = self._get_brush(
            *operator.itemgetter(2, 3)(self._colors[self.style]))

        # Construct the node
        self._build()

    def get_title(self):
        """ Create a title for the node.

        If a pipeline box is contained in the node, the '[...]' synthax will
        be used.
        """
        if self.pbox is None:
            return self.name
        else:
            return "[{0}]".format(self.name)

    def _build(self, margin=5):
        """ Create a node reprensenting a box.

        Parameters
        ----------
        margin: int (optional, default 5)
            the default margin.
        """
        # Create a title for the node
        self.title = QtGui.QGraphicsTextItem(self.get_title(), self)
        font = self.title.font()
        font.setWeight(QtGui.QFont.Bold)
        self.title.setFont(font)
        self.title.setPos(margin, margin)
        self.title.setZValue(2)
        self.title.setParentItem(self)

        # Define the default control position
        control_position = (
            margin + margin + self.title.boundingRect().size().height())

        # Create the input controls
        for input_name in self.input_names:

            # Create the control representation
            control_glyph, control_text = self._create_control(
                input_name, control_position, is_output=False, margin=margin)

            # Update the class parameters
            self.input_controls[input_name] = (control_glyph, control_text)

            # Update the next control position
            control_position += control_text.boundingRect().size().height()

        # Create the output controls
        for output_name in self.output_names:

            # Create the control representation
            control_glyph, control_text = self._create_control(
                output_name, control_position, is_output=True, margin=margin)

            # Update the class parameters
            self.output_controls[output_name] = (control_glyph, control_text)

            # Update the next control position
            control_position += control_text.boundingRect().size().height()

        # Define the box node
        self.box = QtGui.QGraphicsRectItem(self)
        self.box.setBrush(self.background_brush)
        self.box.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.box.setZValue(-1)
        self.box.setParentItem(self)
        self.box.setRect(self.contentsRect())
        self.box_title = QtGui.QGraphicsRectItem(self)
        rect = self.title.mapRectToParent(self.title.boundingRect())
        brect = self.contentsRect()
        brect.setWidth(brect.right() - margin)
        rect.setWidth(brect.width())
        self.box_title.setRect(rect)
        self.box_title.setBrush(self.title_brush)
        self.box_title.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        self.box_title.setParentItem(self)

    def _create_control(self, control_name, control_position, is_output=False,
                        control_width=12, margin=5):
        """ Create a control representation: small glyph and control name.

        Parameters
        ----------
        control_name: str (mandatory)
            the name of the control to render.
        control_position: int (mandatory)
            the position (height) of the control to render.
        control_name: bool (optional, default False)
            an input control glyph is diplayed on the left while an output
            control glyph is displayed on the right.
        control_width: int (optional, default 12)
            the default size of the control glyph.
        margin: int (optional, default 5)
            the default margin.

        Returns
        -------
        control_text: QGraphicsTextItem
            the control text item.
        control_glyph: Control
            the associated control glyph item.
        """
        # Detect if the control is optional
        controls = self.inputs
        if is_output:
            controls = self.outputs
        control = getattr(controls, control_name)
        is_optional = control.optional

        # Create the control representation
        control_text = QtGui.QGraphicsTextItem(self)
        control_text.setHtml(control_name)
        control_name = "{0}:{1}".format(self.name, control_name)
        control_glyph = Control(
            control, control_name, control_text.boundingRect().size().height(),
            control_width, optional=is_optional, parent=self)
        control_text.setZValue(2)
        control_glyph_width = control_glyph.boundingRect().size().width()
        control_text_width = control_text.boundingRect().size().width()
        control_text.setPos(control_glyph_width + margin, control_position)
        if is_output:
            control_glyph.setPos(
                control_glyph_width + margin + control_text_width + margin,
                control_position)
        else:
            control_glyph.setPos(margin, control_position)
        control_text.setParentItem(self)
        control_glyph.setParentItem(self)

        return control_glyph, control_text

    def _get_brush(self, color1, color2):
        """ Create a brush that has a style, a color, a gradient and a texture.

        Parameters
        ----------
        color1, color2: QtGui.QColor (mandatory)
            edge box colors used to define the gradient.
        """
        gradient = QtGui.QLinearGradient(0, 0, 0, 50)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        return QtGui.QBrush(gradient)

    def contentsRect(self):
        """ Returns the area inside the widget's margins.

        Returns
        -------
        brect: QRectF
            the bounding rectangle (left, top, right, bottom).
        """
        first = True
        excluded = []
        for name in ("box", "box_title"):
            if hasattr(self, name):
                excluded.append(getattr(self, name))
        for child in self.childItems():
            if not child.isVisible() or child in excluded:
                continue
            item_rect = self.mapRectFromItem(child, child.boundingRect())
            if first:
                first = False
                brect = item_rect
            else:
                if item_rect.left() < brect.left():
                    brect.setLeft(item_rect.left())
                if item_rect.top() < brect.top():
                    brect.setTop(item_rect.top())
                if item_rect.right() > brect.right():
                    brect.setRight(item_rect.right())
                if item_rect.bottom() > brect.bottom():
                    brect.setBottom(item_rect.bottom())
        return brect

    def boundingRect(self):
        """ Returns the bounding rectangle of the given text as it will appear
        when drawn inside the rectangle beginning at the point (x , y ) with
        width w and height h.

        Returns
        -------
        brect: QRectF
            the bounding rectangle (x, y, w, h).
        """
        brect = self.contentsRect()
        brect.setRight(brect.right())
        brect.setBottom(brect.bottom())
        return brect

    def paint(self, painter, option, widget=None):
        pass

    def mouseDoubleClickEvent(self, event):
        """ If a sub-pipeline is available emit a 'subpipeline_clicked' signal.
        """
        if self.pbox is not None:
            self.scene().subpipeline_clicked.emit(self.name, self.pbox,
                                                  event.modifiers())
            event.accept()
        else:
            event.ignore()

    def add_subpipeline_view(self, pbox, margin=5):
        """ Display the a sub-pipeline box in a node.

        Parameters
        ----------
        pbox: Pbox (mandatory)
            the sub-pipeline box to display.
        """
        # Create a embedded proxy view
        if self.embedded_pbox is None:
            pview = PipelineView(pbox)
            proxy_pview = EmbeddedSubPboxItem(pview)
            pview._graphics_item = weakref.proxy(proxy_pview)
            proxy_pview.setParentItem(self)
            posx = margin + self.box.boundingRect().width()
            proxy_pview.setPos(posx, margin)
            self.embedded_pbox = proxy_pview

        # Change visibility property of the embedded proxy view
        else:
            if self.embedded_pbox.isVisible():
                self.embedded_pbox.hide()
            else:
                self.embedded_pbox.show()


class EmbeddedSubPboxItem(QtGui.QGraphicsProxyWidget):
    """ QGraphicsItem containing a sub-pipeline box view.
    """

    def __init__(self, sub_pipeline_view):
        """ Initialize the EmbeddedSubPboxItem.

        Parameters
        ----------
        sub_pipeline_view: PipelineView (mandatory)
            the sub-pipeline view.
        """
        # Inheritance
        super(EmbeddedSubPboxItem, self).__init__()

        # Define rendering options
        sub_pipeline_view.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        sub_pipeline_view.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        # sub_pipeline_view.setFixedSize(400, 600)

        # Add the sub-pipeline widget
        self.setWidget(sub_pipeline_view)

        # sub_pipeline_view.setSizePolicy(
        #     QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        # self.setSizePolicy(
        #     QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)


class Link(QtGui.QGraphicsPathItem):
    """ A link between boxes.
    """

    def __init__(self, src_position, dest_position, parent=None):
        """ Initilaize the Link class.

        Parameters
        ----------
        src_position: QPointF (mandatory)
            the source control glyph position.
        dest_position: QPointF (mandatory)
            the destination control glyph position.
        """
        # Inheritance
        super(Link, self).__init__(parent)

        # Define the color rendering
        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setBrush(RED_2)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        self.setPen(pen)

        # Draw the link
        path = QtGui.QPainterPath()
        path.moveTo(src_position.x(), src_position.y())
        path.cubicTo(src_position.x() + 100, src_position.y(),
                     dest_position.x() - 100, dest_position.y(),
                     dest_position.x(), dest_position.y())
        self.setPath(path)
        self.setZValue(0.5)

    def update(self, src_position, dest_position):
        """ Update the link extreme positions.

        Parameters
        ----------
        src_position: QPointF (mandatory)
            the source control glyph position.
        dest_position: QPointF (mandatory)
            the destination control glyph position.
        """
        path = QtGui.QPainterPath()
        path.moveTo(src_position.x(), src_position.y())
        path.cubicTo(src_position.x() + 100, src_position.y(),
                     dest_position.x() - 100, dest_position.y(),
                     dest_position.x(), dest_position.y())

        self.setPath(path)


class PipelineScene(QtGui.QGraphicsScene):
    """ Define a scene representing a pipeline box.
    """
    # Signal emitted when a sub pipeline has to be open
    subpipeline_clicked = QtCore.Signal(str, Pbox, QtCore.Qt.KeyboardModifiers)

    def __init__(self, pbox, parent=None):
        """ Initilaize the PipelineScene class.

        Parameters
        ----------
        pbox: Pbox (mandatory)
            pipeline box to be displayed.
        parent: QWidget (optional, default None)
            parent widget.
        """
        # Inheritance
        super(PipelineScene, self).__init__(parent)

        # Class parameters
        self.pipeline = pbox
        self.gnodes = {}
        self.glinks = {}
        self.gpositions = {}

        # Add event to upadate links
        self.changed.connect(self.update_links)

    def update_links(self):
        """ Update the node positions and associated links.
        """
        for node in self.items():
            if isinstance(node, Node):
                self.gpositions[node.name] = node.pos()

        for linkdesc, link in self.glinks.items():
            # Parse the link description
            src_control, dest_control = self.parse_link_description(linkdesc)

            # Get the source and destination nodes/controls
            src_gnode = self.gnodes[src_control[0]]
            dest_gnode = self.gnodes[dest_control[0]]
            src_gcontrol = src_control[1]
            dest_gcontrol = dest_control[1]

            # Update the current link
            src_control_glyph = src_gnode.output_controls[src_gcontrol][0]
            dest_control_glyph = dest_gnode.input_controls[dest_gcontrol][0]
            link.update(
                src_gnode.mapToScene(src_control_glyph.get_control_point()),
                dest_gnode.mapToScene(dest_control_glyph.get_control_point()))

    def draw(self):
        """ Draw the scene representing the pipeline box.
        """
        # Add the pipeline input box
        self.add_box("inputs", outputs=self.pipeline.inputs, inputs=None,
                     style=None, pbox=None)

        # Add the pipeline output box
        self.add_box("outputs", inputs=self.pipeline.outputs, outputs=None,
                     style=None, pbox=None)

        # Add the pipeline box
        for box_name, box in self.pipeline._boxes.items():

            # Define the box type and check if we are dealing with a pipeline
            # box
            pbox = None
            if isinstance(box, Bbox):
                style = "bbox"
            elif isinstance(box, Ibox):
                style = "ibox"
            elif isinstance(box, Pbox):
                style = "pbox"
                pbox = box
            else:
                style = None

            # Add the pipeline box
            self.add_box(box_name, inputs=box.inputs, outputs=box.outputs,
                         active=box.active, style=style, pbox=pbox)

        # If no node position is defined used an automatic setup
        # based on a graph representation of the pipeline
        if self.gpositions == {}:
            scale = 0.0
            for node in self.gnodes.values():
                scale = max(node.box.boundingRect().width(), scale)
                scale = max(node.box.boundingRect().height(), scale)
            scale *= 2.5
            graph, _, _ = self.pipeline._create_graph(
                self.pipeline, flatten=False, add_io=True)
            box_positions = graph.layout(scale=scale)
            for node_name, node_pos in box_positions.items():
                self.gnodes[node_name].setPos(QtCore.QPointF(*node_pos))

        # Create the links between the boxes
        for linkdesc in self.pipeline._links:
            self.add_link(linkdesc)

    def parse_link_description(self, linkdesc):
        """ Parse a link description.

        Parameters
        ----------
        linkdesc: string (mandatory)
            link representation with the source and destination separated
            by '->' and control desriptions of the form
            '<box_name>.<control_name>' or '<control_name>' for pipeline
            input or output controls.

        Returns
        -------
        src_control: 2-uplet
            the source control representation (box_name, control_name).
        dest_control: 2-uplet
            the destination control representation (box_name, control_name).
        """
        # Parse description
        srcdesc, destdesc = linkdesc.split("->")
        src_control = srcdesc.split(".")
        dest_control = destdesc.split(".")

        # Deal with pipeline input and output controls
        if len(src_control) == 1:
            src_control.insert(0, "inputs")
        if len(dest_control) == 1:
            dest_control.insert(0, "outputs")

        return tuple(src_control), tuple(dest_control)

    def add_box(self, name, inputs, outputs, active=True, style=None,
                pbox=None):
        """ Add a box in the graph representation of the pipeline.

        Parameters
        ----------
        name: string (mandatory)
            a name for the box.
        inputs: ControlObject (mandatory)
            the box input controls.
        outputs: ControlObject (mandatory)
            the box output controls.
        active: bool (optional, default True)
            a special color will be applied on the box rendering depending
            of this parameter.
        style: string (optional, default None)
            the style that will be applied to tune the box rendering.
        pbox: casper.pipeline.Pbox (optional, default None)
            the pipeline contained in the created box node.
        """
        # Create the node widget that represents the box
        box_node = Node(name, inputs, outputs, active=active, style=style,
                        pbox=pbox)

        # Update the scene
        self.addItem(box_node)
        node_position = self.gpositions.get(name)
        if node_position is not None:
            box_node.setPos(node_position)
        self.gnodes[name] = box_node

    def add_link(self, linkdesc):
        """ Define a link between two nodes in the graph.

        Parameters
        ----------
        linkdesc: string (mandatory)
            link representation with the source and destination separated
            by '->' and control desriptions of the form
            '<box_name>.<control_name>' or '<control_name>' for pipeline
            input or output controls.
        """
        # Parse the link description
        src_control, dest_control = self.parse_link_description(linkdesc)

        # Get the source and destination nodes/controls
        src_gnode = self.gnodes[src_control[0]]
        dest_gnode = self.gnodes[dest_control[0]]
        src_gcontrol = src_control[1]
        dest_gcontrol = dest_control[1]

        # Create the link
        src_control_glyph = src_gnode.output_controls[src_gcontrol][0]
        dest_control_glyph = dest_gnode.input_controls[dest_gcontrol][0]
        glink = Link(
            src_gnode.mapToScene(src_control_glyph.get_control_point()),
            dest_gnode.mapToScene(dest_control_glyph.get_control_point()))

        # Update the scene
        self.addItem(glink)
        self.glinks[linkdesc] = glink

    def keyPressEvent(self, event):
        """ Display the graph box positions when the 'p' key is pressed.
        """
        super(PipelineScene, self).keyPressEvent(event)
        if not event.isAccepted() and event.key() == QtCore.Qt.Key_P:
            event.accept()
            posdict = dict([(key, (value.x(), value.y()))
                            for key, value in self.gpositions.iteritems()])
            pprint(posdict)

    def helpEvent(self, event):
        """ Display tooltips on controls and links.
        """
        item = self.itemAt(event.scenePos())
        if isinstance(item, Control):
            item.setToolTip("type: {0} - optional: {1}".format(
                item.control.__class__.__name__, item.optional))
        super(PipelineScene, self).helpEvent(event)


class PipelineView(QtGui.QGraphicsView):
    """ Pipeline box representation as a graph (using boxes and arrows).

    Based on Qt QGraphicsView, this can be used as a Qt QWidget.

    Qt signals are emitted:

    * on a double click on a sub-pipeline box to display the sub-pipeline. If
      'ctrl' is pressed a new window is created otherwise the view is
      embedded.
    * on the wheel to zoom in or zoom out.
    * on the kewboard 'p' key to display the box node positions.

    Attributes
    ----------
    scene: PipelineScene
        the main scene.

    Methods
    -------
    __init__
    set_pbox
    zoom_in
    zoom_out
    """
    # Signal emitted when a sub pipeline has to be open
    subpipeline_clicked = QtCore.Signal(str, Pbox, QtCore.Qt.KeyboardModifiers)

    def __init__(self, pbox, parent=None):
        """ Initilaize the PipelineView class.

        Parameters
        ----------
        pbox: Pbox (mandatory)
            pipeline box to be displayed.
        parent: QWidget (optional, default None)
            parent widget.
        """
        # Inheritance
        super(PipelineView, self).__init__(parent)

        # Class parameters
        self.scene = None

        # Check that we have a pbox
        if not isinstance(pbox, Pbox):
            raise Exception("'{0}' is not a pipeline box {1}.".format(
                pipeline.id, type(Pbox)))

        # Create the graph representing the pipeline box.
        self.set_pbox(pbox)

    def set_pbox(self, pbox):
        """ Assigns a new pipeline to the view.

        Parameters
        ----------
        pbox: Pbox (mandatory)
            pipeline box to be displayed.
        """
        # Define the pipeline box positions
        if hasattr(pbox, "_box_positions"):
            box_positions = dict(
                (box_name, QtCore.QPointF(*box_position))
                for box_name, box_position in pbox._box_positions.items())
        else:
            box_positions = {}

        # Create the scene
        self.scene = PipelineScene(pbox, self)
        self.scene.gpositions = box_positions
        self.scene.draw()

        # Update the current view
        self.setWindowTitle(pbox.id)
        self.setScene(self.scene)

        # Try to initialize the current view scale factor
        if hasattr(pbox, "scale"):
            self.scale(pbox.scale, pbox.scale)

        # Define signals
        self.scene.subpipeline_clicked.connect(self.subpipeline_clicked)
        self.scene.subpipeline_clicked.connect(self.display_subpipeline)

    def zoom_in(self):
        """ Zoom the view in by applying a 1.2 zoom factor.
        """
        self.scale(1.2, 1.2)

    def zoom_out(self):
        """ Zoom the view out by applying a 1 / 1.2 zoom factor.
        """
        self.scale(1.0 / 1.2, 1.0 / 1.2)

    def display_subpipeline(self, node_name, pbox, modifiers):
        """ Event to display the selected sub-pipeline.

        If 'ctrl' is pressed the a new window is created, otherwise the new
        view will be embedded in its parent node box.

        Parameters
        ----------
        node_name: str (mandatory)
            the node name.
        pbox: Pbox (mandatory)
            the sub-pipeline box to display.
        """
        # Open a new window
        if modifiers & QtCore.Qt.ControlModifier:
            pview = PipelineView(pbox)
            QtCore.QObject.setParent(pview, self.window())
            pview.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            pview.setWindowTitle(node_name)
            pview.show()

        # Embedded sub-pipeline inside its parent node
        else:
            node = self.scene.gnodes.get(node_name)
            node.add_subpipeline_view(pbox)

    def wheelEvent(self, event):
        """ Change the scene zoom factor.
        """
        item = self.itemAt(event.pos())
        if not isinstance(item, QtGui.QGraphicsProxyWidget):
            if event.delta() < 0:
                self.zoom_out()
            else:
                self.zoom_in()
            event.accept()
        else:
            super(PipelineView, self).wheelEvent(event)
