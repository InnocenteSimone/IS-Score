from PyQt5.QtWidgets import QFileSystemModel

class FolderTreeModel(QFileSystemModel):

    def __init__(self, root_path):
        super().__init__()
        if root_path is not None:
            self.setModelRootPath(root_path)

    def setModelRootPath(self, root_path):
        self.setRootPath(root_path)
        self.root_path = root_path