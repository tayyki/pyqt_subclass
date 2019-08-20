from qtswitch import QtCore, QtGui


# Globals if 'CategoryDelegate' is used.
IsCategoryRole = QtCore.Qt.UserRole
ParentRole = QtCore.Qt.UserRole + 1


class CategoryDelegate(QtGui.QStyledItemDelegate):
    # https://stackoverflow.com/questions/56999157/check-an-item-that-effects-on-a-certain-set-of-items-within-qlistwidget
    def editorEvent(self, event, model, option, index):
        old_state = model.data(index, QtCore.Qt.CheckStateRole)
        res = super(CategoryDelegate, self).editorEvent(
            event, model, option, index
        )
        current_state = model.data(index, QtCore.Qt.CheckStateRole)
        if old_state != current_state:
            if index.data(IsCategoryRole):
                pix = QtCore.QPersistentModelIndex(index)
                for i in range(model.rowCount()):
                    ix = model.index(i, 0)
                    if pix == ix.data(ParentRole):
                        model.setData(
                            ix, current_state, QtCore.Qt.CheckStateRole
                        )
        return res


class CustomListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        super(CustomListWidget, self).__init__(parent=parent)

        # Uncomment: Only if you would want to have categories within List Widget
        # delegate = CategoryDelegate(self)
        # self.setItemDelegate(delegate)

        # self.setStyleSheet(
        #     """ QListWidget:item:selected:active {
        #              background: blue;
        #         }
        #         QListWidget:item:selected:!active {
        #              background: gray;
        #         }
        #         QListWidget:item:selected:disabled {
        #              background: gray;
        #         }
        #         QListWidget:item:selected:!disabled {
        #              background: blue;
        #         }
        #     """
        # )

    def initial_selection(self):
        """Always selects the first list item if any.
        """
        if not self.derive_list_items_num():
            self.item(0).setSelected(True)
            self.setFocus()


    def get_current_selected_item(self):
        """Derive currently selected item.

        Returns:
            QListWidgetItem: List item.
        """
        return self.currentItem()

    def get_selected_text(self):
        """Derive text name of current selected list item.

        Returns:
            str: Name of the list item.
        """
        return self.get_current_selected_item.text()

    def get_selected_row(self):
        """Derive row number of current selected list item.

        Returns:
            int: Row number of currently selected item.
        """
        return self.currentRow()

    def derive_list_items_num(self):
        """Derive the number of list items.

        Returns:
            int: The number of items found in the QListWidget.
        """
        return self.count()

    def create_checkable_item(self, item_text, is_editable=False):
        """Creates checkable list item.

        List item will be unchecked upon creation and User can define if it
        needs to be editable.

        Args:
            item_text (str): Name for created list item.

        Keyword Args:
            is_editable (bool): Allows list item to be editable.
                False by default.

        Returns:
            QListWidgetItem: List-widget item.
        """
        list_item = QtGui.QListWidgetItem(item_text)
        if is_editable:
            list_item.setFlags(
                list_item.flags()
                | QtCore.Qt.ItemIsUserCheckable
                | QtCore.Qt.ItemIsEditable
            )
        else:
            list_item.setFlags(
                list_item.flags()
                | QtCore.Qt.ItemIsUserCheckable
            )
        list_item.setCheckState(QtCore.Qt.Unchecked)
        return list_item

    def contextMenuEvent(self, event):
        """Right-click menu action on list items.

        # https://stackoverflow.com/questions/57048781/access-delegate-class-from-qaction-trigger

        Args:
            event ():
        """
        list_menu = QtGui.QMenu()
        it = self.itemAt(self.viewport().mapFromGlobal(QtGui.QCursor().pos()))
        update_cat_items = QtGui.QAction("Check all or none", self)
        # update_cat_items.triggered.connect(self.update_opts)
        list_menu.addAction(update_cat_items)
        list_menu.exec_(QtGui.QCursor().pos())

    def remove_list_item(self):
        """Remove selected list item."""
        for list_item in self.selectedItems():
            self.takeItem(self.row(list_item))



class MainApp(QtGui.QWidget):
    def __init__(self):
        super(MainApp, self).__init__()

        self._ui = CustomListWidget()

        ########################################################################

        layout = QtGui.QVBoxLayout()
        self.btn = QtGui.QPushButton("TEST BTN.")
        layout.addWidget(self._ui)
        layout.addWidget(self.btn)

        test_items = ["blah", "bleh", "bloop"]
        for item in test_items:
            aaa = self._ui.create_checkable_item(item)
            self._ui.addItem(aaa)

        self.setLayout(layout)

        ########################################################################

        self.setup_connections()
        self._ui.initial_selection()


    def setup_connections(self):
        self.btn.clicked.connect(self.button_test)

    def button_test(self):
        self._ui.remove_list_item()




if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    w = MainApp()
    w.show()
    sys.exit(app.exec_())
