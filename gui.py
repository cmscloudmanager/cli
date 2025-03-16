import uuid

from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QStyleFactory, QVBoxLayout)


class WidgetGallery(QDialog):
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())

        self.deploymentIdLineEdit = QLineEdit('')
        self.deploymentIdLineEdit.setReadOnly(True)
        deploymentIdLabel = QLabel("&Deployment ID:")
        deploymentIdLabel.setBuddy(self.deploymentIdLineEdit)
        deploymentIdButton = QPushButton("Regenerate")
        deploymentIdButton.clicked.connect(self.regenerateDeploymentId)

        deployButton = QPushButton("Deploy")

        mainLayout = QVBoxLayout()
        deploymentIdLayout = QVBoxLayout()
        deploymentIdLayout.addWidget(deploymentIdLabel)
        deploymentIdLayout.addWidget(self.deploymentIdLineEdit)
        deploymentIdLayout.addWidget(deploymentIdButton)
        mainLayout.addLayout(deploymentIdLayout)
        apiSettingsLayout = QHBoxLayout()
        apiSettingsLayout.addWidget(self.createProviderGroupBox())
        apiSettingsLayout.addWidget(self.createDNSGroupBox())
        mainLayout.addLayout(apiSettingsLayout)
        mainLayout.addWidget(self.createServerGroupBox())
        mainLayout.addWidget(self.createWordPressGroupBox())
        mainLayout.addWidget(deployButton)
        self.setLayout(mainLayout)

        self.setWindowTitle("CMS Cloud Manager")

    def regenerateDeploymentId(self):
        self.deploymentIdLineEdit.setText(uuid.uuid4().hex)

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        self.changePalette()

    def createProviderGroupBox(self):
        groupBox = QGroupBox("Provider Settings")

        providerComboBox = QComboBox()
        providerComboBox.addItem("Hetzner Cloud")

        providerLabel = QLabel("&Provider:")
        providerLabel.setBuddy(providerComboBox)

        apiTokenLineEdit = QLineEdit('')
        apiTokenLineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        apiTokenLabel = QLabel("&API Token:")
        apiTokenLabel.setBuddy(apiTokenLineEdit)

        layout = QVBoxLayout()
        layout.addWidget(providerLabel)
        layout.addWidget(providerComboBox)
        layout.addWidget(apiTokenLabel)
        layout.addWidget(apiTokenLineEdit)
        layout.addStretch(1)
        groupBox.setLayout(layout)
        return groupBox

    def createDNSGroupBox(self):
        groupBox = QGroupBox("DNS Settings")

        providerComboBox = QComboBox()
        providerComboBox.addItem("Hetzner DNS")
        providerComboBox.setEnabled(False)
        providerLabel = QLabel("&Provider:")
        providerLabel.setBuddy(providerComboBox)

        apiTokenLineEdit = QLineEdit('')
        apiTokenLineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        apiTokenLineEdit.setEnabled(False)
        apiTokenLabel = QLabel("&API Token:")
        apiTokenLabel.setBuddy(apiTokenLineEdit)

        enableDnsSettings = QCheckBox("&Enable DNS Management")
        enableDnsSettings.toggled.connect(providerComboBox.setEnabled)
        enableDnsSettings.toggled.connect(apiTokenLineEdit.setEnabled)

        layout = QVBoxLayout()
        layout.addWidget(enableDnsSettings)
        layout.addWidget(providerLabel)
        layout.addWidget(providerComboBox)
        layout.addWidget(apiTokenLabel)
        layout.addWidget(apiTokenLineEdit)
        layout.addStretch(1)
        groupBox.setLayout(layout)
        return groupBox

    def createServerGroupBox(self):
        groupBox = QGroupBox("Server Settings")

        nameLineEdit = QLineEdit('')
        nameLabel = QLabel("&Name:")
        nameLabel.setBuddy(nameLineEdit)

        instanceComboBox = QComboBox()
        instanceComboBox.addItem("CX22")
        instanceComboBox.addItem("CX32")
        instanceComboBox.addItem("CX42")
        instanceComboBox.addItem("CX52")
        instanceLabel = QLabel("&Instance Type:")
        instanceLabel.setBuddy(instanceComboBox)

        osComboBox = QComboBox()
        osComboBox.addItem("Debian")
        osComboBox.addItem("Ubuntu")
        osLabel = QLabel("&Operating System:")
        osLabel.setBuddy(osComboBox)

        sshKeyLineEdit = QLineEdit('')
        sshKeyLabel = QLabel("&SSH Key:")
        sshKeyLabel.setBuddy(sshKeyLineEdit)

        leMailLineEdit = QLineEdit('')
        leMailLabel = QLabel("&Let's Encrypt E-Mail:")
        leMailLabel.setBuddy(leMailLineEdit)

        layout = QVBoxLayout()
        layout.addWidget(nameLabel)
        layout.addWidget(nameLineEdit)
        layout.addWidget(instanceLabel)
        layout.addWidget(instanceComboBox)
        layout.addWidget(osLabel)
        layout.addWidget(osComboBox)
        layout.addWidget(sshKeyLabel)
        layout.addWidget(sshKeyLineEdit)
        layout.addWidget(leMailLabel)
        layout.addWidget(leMailLineEdit)
        layout.addStretch(1)
        groupBox.setLayout(layout)
        return groupBox

    def createWordPressGroupBox(self):
        groupBox = QGroupBox("WordPress Settings")

        hostnameLineEdit = QLineEdit('')
        hostnameLabel = QLabel("&Hostname:")
        hostnameLabel.setBuddy(hostnameLineEdit)

        layout = QVBoxLayout()
        layout.addWidget(hostnameLabel)
        layout.addWidget(hostnameLineEdit)
        layout.addStretch(1)
        groupBox.setLayout(layout)
        return groupBox


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    gallery = WidgetGallery()
    gallery.setMinimumSize(600, 400)
    gallery.show()
    sys.exit(app.exec())