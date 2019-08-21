from qtswitch import QtGui, QtCore
import sys

from collections import defaultdict, OrderedDict
from functools import partial

import logging
LOGGER = logging.getLogger(__name__)

# https://stackoverflow.com/questions/31342228/pyqt-tree-widget-adding-check-boxes-for-dynamic-removal
'''
Expected layout:

> category itemA
    --- item1
    --- item2
    --- item3
> category itemB
    --- item1
    --- item2

'''

IsNewItemRole = QtCore.Qt.UserRole + 1000
IsPageRole = QtCore.Qt.UserRole + 2000


class CustomTreeDelegate(QtGui.QStyledItemDelegate):
    # https://stackoverflow.com/questions/57486888/derive-and-set-color-to-the-index-of-newly-added-children
    @property
    def text_color(self):
        """
        """
        if not hasattr(self, "_text_color"):
            self._text_color = QtGui.QColor()
        return self._text_color

    @text_color.setter
    def text_color(self, color):
        """Sets QColor towards object.

        Args:
            color (QtGui.QColor): RGB color values.
        """
        self._text_color = color

    def initStyleOption(self, option, index):
        """Change the font color only if item is a new added item.

        Args:
            option ():
            index (QModelIndex?)
        """
        super(CustomTreeDelegate, self).initStyleOption(option, index)
        if self.text_color.isValid() and index.data(IsNewItemRole):
            option.palette.setBrush(QtGui.QPalette.Text, self.text_color)


class CustomTreeWidgetItem(QtGui.QTreeWidgetItem):
    """Initialization class for QTreeWidgetItem creation.

    Args:
        widget (QtGui.QTreeWidget): To append items into.
        text (str): Input name for QTreeWidgetItem.
        is_tristate (bool): Should it be a tri-state checkbox. False by default.
    """
    def __init__(self, parent=None, text=None, is_tristate=False, is_new_item=False):
        super(CustomTreeWidgetItem, self).__init__(parent)

        self.setText(0, text)
        # flags = QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsUserCheckable

        if is_tristate:
            # flags |= QtCore.Qt.ItemIsTristate

            # Solely for the Parent item
            self.setFlags(
                self.flags()
                | QtCore.Qt.ItemIsTristate
                | QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsUserCheckable
            )
        else:
            self.setFlags(
                self.flags()
                | QtCore.Qt.ItemIsEditable
                | QtCore.Qt.ItemIsUserCheckable
            )
            self.setCheckState(0, QtCore.Qt.Unchecked)

        self.setData(0, IsNewItemRole, is_new_item)

    def setData(self, column, role, value):
        """Override QTreeWidgetItem setData function.

        QTreeWidget does not have a signal that defines when an item has been
        checked/ unchecked. And so, this method will emits the signal as a
        means to handle this.

        Args:
            column (int): Column value of item.
            role (int): Value of Qt.ItemDataRole. It will be Qt.DisplayRole or
                Qt.CheckStateRole
            value (int or unicode): 
        """
        state = self.checkState(column)
        QtGui.QTreeWidgetItem.setData(self, column, role, value)
        if (role == QtCore.Qt.CheckStateRole and
                state != self.checkState(column)):
            tree_widget = self.treeWidget()
            if isinstance(tree_widget, CustomTreeWidget):
                tree_widget.itemToggled.emit(self, column)


class CustomTreeWidget(QtGui.QTreeWidget):
    """Initialization class for QTreeWidget creation.

    Args:
        widget ():
    """
    # itemToggled = QtCore.pyqtSignal(QtGui.QTreeWidgetItem, bool)
    itemToggled = QtCore.Signal(QtGui.QTreeWidgetItem, bool)

    selectionItemChanged = QtCore.Signal(bool)
    contentUpdates = QtCore.Signal()

    def __init__(self, widget=None):
        super(CustomTreeWidget, self).__init__(widget)

        self.rename_counter = False

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_custom_menu)

        # self.itemToggled.connect(self.handleItemToggled)
        self.currentItemChanged.connect(self.selection_item_changed)
        self.itemChanged.connect(self.tree_item_changed)
        self.itemDoubleClicked.connect(self.tree_item_double_clicked)

    def selection_item_changed(self, current, previous):
        """Overrides widget's default signal.

        Emiited when current item selection is changed. This will also toggles
        the state of `self.add_child_btn`.
        If a child item is selected, the "Add Child" button will be disabled.

        Args:
            current (CustomTreeWidgetItem): Currently selected item.
            previous (CustomTreeWidgetItem or None): Previous selected item.
        """
        state = True
        if not current or current.parent():
            state = False

        self.selectionItemChanged.emit(state)

    def tree_item_changed(self, item, column):
        """Overrides widget's default signal.

        Emitted when the contents of the selected item in the column changes.

        Args:
            item (CustomTreeWidgetItem): Selected item.
            column (int): Column value of the selected item.
        """
        if self.rename_counter and self.prev_name != item.text(column):
            print '>>> renaming performed..'
            self.rename_counter = False
            item.setData(0, IsNewItemRole, True)

            self.contentUpdates.emit()

        #>>> TODO - To do a double take where `contentUpdates` may not be
        # emitting correctly.
        elif item.data(column, IsNewItemRole):
            print '>>> item is already an newitemrole'
            return

        # if item.checkState(column) == QtCore.Qt.Checked:
        #     print('Item Checked')
        # elif item.checkState(column) == QtCore.Qt.Unchecked:
        #     print('Item Unchecked')

        # elif item.text(0) and self._startup:
        #     print 'Item Name changed'
        #     item.setData(0, IsNewItemRole, True)
        # print

    def tree_item_double_clicked(self, item, column):
        """Overrides widget's default signal.

        Emitted when User performs double clicks inside the widget.

        Args:
            item (CustomTreeWidgetItem): Selected item.
            column (int): Column value of the selected item.
        """
        # print '>>> tree item double clicked...'
        self.prev_name = item.text(column)
        self.rename_counter = True

    def show_custom_menu(self, pos):
        """Display custom context menu."""
        base_node = self.itemAt(pos)
        if base_node is None:
            return

        qmenu = QtGui.QMenu(self)
        remove_action = QtGui.QAction("Remove item", self)
        remove_action.triggered.connect(self.remove_selected_item)
        qmenu.addAction(remove_action)

        #>>>
        move_up_action = QtGui.QAction("Move Up", self)
        move_up_action.triggered.connect(partial(self.move_item, direction="up"))
        qmenu.addAction(move_up_action)

        move_down_action = QtGui.QAction("Move down", self)
        move_down_action.triggered.connect(partial(self.move_item, direction="down"))
        qmenu.addAction(move_down_action)


        # The following options are only effected for top-level items
        # top-level items do not have `parent()`
        if base_node.parent() is None:
            add_new_child_action = QtGui.QAction("Add new sub item", self)
            add_new_child_action.triggered.connect(
                partial(self.add_new_child_item, base_node)
            )
            # qmenu.addAction(add_new_child_action)
            qmenu.insertAction(remove_action, add_new_child_action)

        qmenu.exec_(self.mapToGlobal(pos))

    def move_item(self, direction=""):
        """Move selected item up.

        If top-level item is selected, the child items within will be moved
        along with it.
        
        Args:
            direction (str): Either 'up' or 'down'. Denotes the direction of
                the new item placement.
        """
        
        selected = self.currentItem()

        # Top-Level item in selection
        if selected.parent() is None:
            print '>>> parent'
            selected_index = self.indexOfTopLevelItem(selected)
            selected_item = self.topLevelItem(selected_index)
            self.takeTopLevelItem(selected_index)

            root_item = self.invisibleRootItem()
            top_level_count = root_item.childCount()

            if direction == "up":
                new_index = selected_index - 1

                if new_index < 0:
                    new_index = 0

            elif direction == "down":
                new_index = selected_index + 1

                if new_index > top_level_count:
                    new_index = top_level_count

            self.insertTopLevelItem(new_index, selected_item)
            selected_item.setExpanded(True)

        # Child item in selection
        else:
            print '>>> child'
            parent_item = selected.parent()
            selected_index = parent_item.indexOfChild(selected)
            selected_item = parent_item.takeChild(selected_index)

            child_count = parent_item.childCount()

            if direction == "up":
                new_index = selected_index - 1

                if new_index < 0:
                    new_index = 0

            elif direction == "down":
                new_index = selected_index + 1

                if new_index > child_count:
                    new_index = child_count

            parent_item.insertChild(new_index, selected_item)

        self.setCurrentItem(selected_item)


    def add_item_dialog(self, title):
        """Input dialog for creation of new Parent or Sub items.

        Args:
            title (str): Title indication to be display in Dialog for parent/
                sub items creation.

        Returns:
            str: Name of new created item.
        """
        text, ok = QtGui.QInputDialog.getText(
            self,
            "Add {0} Item".format(title),
            "Enter name for {0}-Item:".format(title)
        )
        if ok and text != "":
            return text

    def add_new_parent_item(self):
        """Creation of new parent item."""
        input_text = self.add_item_dialog("Parent")
        top_level_names = self.derive_top_level_names()

        if input_text:

            if input_text in top_level_names:
                print "'{0}' already exists!".format(input_text)
                return

            new_item = CustomTreeWidgetItem(
                self, input_text, is_tristate=True, is_new_item=True
            )

            self.setCurrentItem(new_item)

    def add_new_child_item(self, base_node):
        """Creation of new child item, to be populated under parent item.

        Args:
            base_node (CustomTreeWidgetItem): Parent node for child item to be
                added into.
        """
        input_text = self.add_item_dialog("Sub")
        child_item_names = self.derive_child_names_from_top_level(base_node)

        if input_text:

            if input_text in child_item_names:
                print "'{0}' already existed under {1}".format(
                    input_text,
                    base_node.text(0)
                )
                return

            it = CustomTreeWidgetItem(base_node, input_text, is_new_item=True)
            self.setItemExpanded(base_node, True) # This is only available in Qt4
            # base_node.setExpanded(True)
            it.setData(0, IsNewItemRole, True)

            self.setCurrentItem(it)

    def is_top_level_item(self):
        """Check if currently selected item is a top-level item.

        Returns:
            bool: True if selected item is top-level item. False if otherwise.
        """
        result = True
        if self.currentItem().parent():
            result = False
        return result

    def remove_selected_item(self):
        """Removes entry in TreeWidget.

        This method applies to both parent and child items.
        """
        root = self.invisibleRootItem()
        for item in self.selectedItems():
            (item.parent() or root).removeChild(item)

    def get_selected_text(self):
        """Get the text naming of selected item.
        
        If parent item is selected, only the name will be return.
        If child item is selected, it will returns with the prefix of its parent
        naming, eg. 'parentName/childName'.

        Retuns:
            str: Name of selected item.
        """
        get_selected = self.selectedItems()
        if get_selected:
            base_node = get_selected[0]
            item_name = base_node.text(0)

            # When child-item is selected
            if base_node.parent():
                item_name = "{0}/{1}".format(base_node.parent().text(0), item_name)

            return item_name

    def get_selected_child_count(self):
        """Derive number of child items under top-level item.

        Returns:
            int: Number of child items found under parent.
        """
        get_selected = self.selectedItems()
        if get_selected:
            base_node = get_selected[0]
            return base_node.childCount()

    def derive_top_level_names(self):
        """Derive top-level items' names.

        Returns:
            list(str): List of top-level items' name.
        """
        root_item = self.invisibleRootItem()
        top_level_count = root_item.childCount()
        top_item_names = []

        for num in range(top_level_count):
            top_item_names.append(root_item.child(num).text(0))

        return top_item_names

    def derive_child_names_from_top_level(self, base_node):
        """Derive child items' names from given top-level item.

        Args:
            base_node (CustomTreeWidgetItem): Selected parent node.

        Returns:
            list(str): List of child items' name found within the parent node.
        """
        child_count = base_node.childCount()
        child_names = []
        for num in range(child_count):
            child_names.append(base_node.child(num).text(0))
        return child_names

    def derive_tree_items(self, mode="all"):
        """Derive items based on specified mode chosen.

        Keyword Args: 
            mode (str): Determines what items to derive. Defaults to `all`.
                There are 3 modes to choose from:
                    * "all"       - Get all items within the widget.
                    * "checked"   - Get only checked items within the widget.
                    * "unchecked" - Get only unchecked items within the widget.

        Returns:
            dict: Contains names of top-level items and its sub items. Contents
                are returned in ordered placement as seen in 

                ..code-block:: json
                        {
                            'topA': [
                                'a101',
                                'a102'
                            ],
                            'topB': [
                                'b101'
                            ]
                        }
        """
        # all_items = defaultdict(list)
        all_items = OrderedDict()
        
        root_item = self.invisibleRootItem()
        top_level_count = root_item.childCount()

        for i in range(top_level_count):
            top_level_item = root_item.child(i)
            top_level_item_name = str(top_level_item.text(0))
            child_num = top_level_item.childCount()

            all_items[top_level_item_name] = []

            for n in range(child_num):
                child_item = top_level_item.child(n)
                child_item_name = str(child_item.text(0)) or ""

                if mode == "all":
                    # all_items[top_level_item.text(0)].append(child.text(0))
                    all_items[top_level_item_name].append(child_item_name)
                
                elif mode == "checked":
                    if child_item.checkState(0) == QtCore.Qt.Checked:
                        # all_items[top_level_item.text(0)].append(child_item.text(0))
                        all_items[top_level_item_name].append(child_item_name)

                elif mode == "unchecked":
                    if child_item.checkState(0) == QtCore.Qt.Unchecked:
                        # all_items[top_level_item.text(0)].append(child_item.text(0))
                        all_items[top_level_item_name].append(child_item_name)

        return all_items


    ####################################################################################################

    # TBC
    def handleItemToggled(self, item, column):
        """Handle list item(s) when it is checked/ unchecked.

        Args:
            item ():
            column (int): 
        """
        # http://stackoverflow.com/questions/13662020/how-to-implement-itemchecked-and-itemunchecked-signals-for-qtreewidget-in-pyqt4
        # print '>>> ItemChecked', int(item.checkState(column))
        # print item.text(column)

        item_name = item.text(column)
        # top-level node
        if item.parent():
            item_name = "{0}/{1}".format(item.parent().text(column), item_name)

        # Returns both top and sub item if the top is checked...

        return item_name

    # TBC
    def set_background_color(self, color_text=""):
        self.setStyleSheet("""QTreeWidget{background: {0};}""".format(color_text))

    #TBC
    def make_checkbox_more_visible(self):
        """In Maya, the background color of the QTreeWidget are changed to conform
        to Maya standards. Adding on, as the outline of the checkboxes are black
        in color in which it is bledning in with Maya (almost black) background
        that makes it hard to visualize if there is a checkbox.

        This method will cause the outline color to appear in white.
        """
        # https://stackoverflow.com/questions/54655382/change-the-style-of-a-checkbox-in-a-qtreewidget-without-affecting-the-check-mark
        file_tree_palette = QtGui.QPalette()
        file_tree_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(255, 255, 255))
        # file_tree_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(30, 30, 30))
        # file_tree_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(93, 93, 93))
        self.setPalette(file_tree_palette)

    #TBC
    def move_item_multi(self, direction=""):
        # only if multi selection is set
        selected = self.selectedItems()
        for s in selected:
            if s.parent() is None:
                selected_index = self.indexOfTopLevelItem(s)
                selected_item = self.topLevelItem(selected_index)
                self.takeTopLevelItem(selected_index)

                root_item = self.invisibleRootItem()
                top_level_count = root_item.childCount()

                if direction == "up":
                    new_index = selected_index - 1

                    if new_index < 0:
                        new_index = 0

            self.insertTopLevelItem(new_index, selected_item)
            selected_item.setExpanded(True)
            self.setCurrentItem(s)


    # END OF QTREEWIDGET TBC #

    ####################################################################################################



####################################################################################################
####################################################################################################

### without subclass ###
def main_without_subclass(): 
    app = QtGui.QApplication(sys.argv)
    tree = QtGui.QTreeWidget ()
    headerItem  = QtGui.QTreeWidgetItem()
    item    = QtGui.QTreeWidgetItem()

    for i in xrange(3):
        parent = QtGui.QTreeWidgetItem(tree)
        parent.setText(0, "Parent {}".format(i))
        parent.setFlags(parent.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
        
        for x in xrange(5):
            child = QtGui.QTreeWidgetItem(parent)
            child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
            child.setText(0, "Child {}".format(x))
            child.setCheckState(0, QtCore.Qt.Unchecked)
    
    tree.show() 
    sys.exit(app.exec_())


### with subclass ###
def main():
    app = QtGui.QApplication(sys.argv)
    tree = QtGui.QTreeWidget()
    tree.header().hide()

    for i in xrange(3):
        parent_name = "Parent {}".format(i)
        parent = CustomTreeWidgetItem(tree, parent_name, is_tristate=True)
        
        for x in xrange(5):
            child_name = "Child {}".format(x)
            child = CustomTreeWidgetItem(parent, child_name)
            child.setCheckState(0, QtCore.Qt.Unchecked)
    
    tree.show() 
    sys.exit(app.exec_())


class MainApp(QtGui.QWidget):
    def __init__(self, parent=None):
        super(MainApp, self).__init__(parent)

        # test_dict = {
        #     "menuA": ["a101", "a102"],
        #     "menuC": ["c101", "c102", "c103"],
        #     "menuB": ["b101"],
        # }
        test_dict = {
            "pageA" :{
                "menuA": ["a101", "a102"],
            },
            "pageBC": {
                "menuC": ["c101", "c102", "c103"],
                "menuB": ["b101"]
            },
        }
        # test_dict = {}

        # self.rename_counter = False
        # self._startup = False
        # self.prev_name = None
        self._diff_highlight = False
        self._tree = CustomTreeWidget()
        self._tree.header().hide()
        self._tree_delegate = CustomTreeDelegate(self._tree)
        self._tree.setItemDelegate(self._tree_delegate)

        # QTreeWidget default signals override
        self._tree.selectionItemChanged.connect(self.check_selection)
        self._tree.contentUpdates.connect(self.update_dictionary)

        # for pk, pv in sorted(test_dict.items()):
        #     parent = CustomTreeWidgetItem(self._tree, pk, is_tristate=True)
        #     for c in pv:
        #         child = CustomTreeWidgetItem(parent, c)

        for page_name, page_contents in test_dict.items():
            # page_item = PageHeaderItem(self._tree, page_name)
            for pk, pv in page_contents.items():
                parent = CustomTreeWidgetItem(self._tree, pk, is_tristate=True)
                for c in pv:
                    child = CustomTreeWidgetItem(parent, c)


        # Expand the hierarchy by default
        self._tree.expandAll()
        #>>> only if multi-selection is required
        # self._tree.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        add_items_layout = QtGui.QHBoxLayout()
        self.add_parent_btn = QtGui.QPushButton("Add Parent")
        self.add_child_btn = QtGui.QPushButton("Add Child")
        add_items_layout.addWidget(self.add_parent_btn)
        add_items_layout.addWidget(self.add_child_btn)

        tree_layout = QtGui.QVBoxLayout()
        self.btn1 = QtGui.QPushButton("TEST BTN1")
        self.btn2 = QtGui.QPushButton("TEST BTN2")
        tree_layout.addWidget(self._tree)
        tree_layout.addLayout(add_items_layout)
        tree_layout.addWidget(self.btn1)
        tree_layout.addWidget(self.btn2)


        self.list_widget = QtGui.QListWidget()
        aaa = ['a', 'b', 'c']
        for a in aaa:
            self.list_widget.addItem(a)


        main_layout = QtGui.QHBoxLayout()
        main_layout.addLayout(tree_layout)
        main_layout.addWidget(self.list_widget)
        
        # self.setLayout(tree_layout)
        self.setLayout(main_layout)

        self.setup_connections()

        self._startup = True
        self.initial_selection()

        if not test_dict:
            self.add_child_btn.setEnabled(False)

    def setup_connections(self):
        self.btn1.clicked.connect(self.button1_test)
        self.btn2.clicked.connect(self.button2_test)

        self.add_parent_btn.clicked.connect(self.add_parent_item)
        self.add_child_btn.clicked.connect(self.add_child_item)

    def initial_selection(self):
        """Ensure selection in CustomTreeWidget during startup.

        Only the first item will be selected.
        """
        root_item = self._tree.invisibleRootItem()
        if root_item.childCount():
            self._tree.setCurrentItem(root_item.child(0))


    def add_parent_item(self):
        self._tree.add_new_parent_item()

    def add_child_item(self):
        self._tree.add_new_child_item(self._tree.currentItem())


    def highlight_new_items(self):
        """Highlight new added items upon toggle.
        """
        if not self._diff_highlight:
            self._tree_delegate.text_color = QtGui.QColor(255, 0, 0)
            self._diff_highlight = True
        else:
            # Reset it back
            self._tree_delegate.text_color = QtGui.QColor()
            self._diff_highlight = False
        
        self._tree.viewport().update()

    def check_selection(self, value):
        self.add_child_btn.setEnabled(value)

    def update_dictionary(self):
        print '>>> update: ', self._tree.derive_tree_items()


    ########################################################################
    # Buttons Test                                                         #
    ########################################################################

    def button1_test(self):
        print '>>> Button1 test'
        # aaa = self._tree.derive_tree_items()
        # self.qmenu = QCustomMenu(title='', parent=self)

        # for pk, pv in aaa.items():
        #     base_qmenu = QCustomMenu(title=pk, parent=self)
        #     test_action = QtGui.QAction(pk, self)
        #     test_action.setMenu(base_qmenu)
        #     self.qmenu.addAction(test_action)

        #     for v in pv:
        #         action = QSubAction(v, self)
        #         base_qmenu.addAction(action)

        # self.qmenu.exec_(QtGui.QCursor.pos())

        print self._tree.currentItem().data(0, IsNewItemRole)



    def button2_test(self):
        print '>>> Button2 test'
        # print self._tree.derive_tree_items()
        #self.highlight_new_items()

        self._tree.currentItem().setData(0, IsNewItemRole, None)



class QSubAction(QtGui.QAction):
    def __init__(self, text="", parent=None):
        super(QSubAction, self).__init__(text, parent)
        self.setCheckable(True)
        self.setChecked(True)


class QCustomMenu(QtGui.QMenu):
    """Customized QMenu."""

    def __init__(self, title, parent=None):
        super(QCustomMenu, self).__init__(title=str(title), parent=parent)
        self.setup_menu()

    def mousePressEvent(self,event):
        action = self.activeAction()
        if not isinstance(action,QSubAction) and action is not None:
            action.trigger()
            return
        elif isinstance(action,QSubAction):
            action.toggle()
            return
        return QtGui.QMenu.mousePressEvent(self,event)
    def setup_menu(self):
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

    def contextMenuEvent(self, event):
        no_right_click = [QAddAction]
        if any([isinstance(self.actionAt(event.pos()), instance) for instance in no_right_click]):
            return
        pos = event.pos()

    def addAction(self, action):
        super(QCustomMenu, self).addAction(action)




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    w = MainApp()
    w.show()
    sys.exit(app.exec_())
