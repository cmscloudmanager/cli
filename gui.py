#!/usr/bin/env python

import uuid

from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QStyleFactory, QVBoxLayout)

from configuration import Configuration
from server_providers import ServerProvider
from dns_providers import DnsProvider
from prepare_server_and_run_ansible import Server

class WidgetGallery(QDialog):

    config = Configuration.from_manifest("empty.yml")

    def onClick(self):
        server_provider = ServerProvider(self.config)

        server_info = server_provider.fetch_provisioned_server()
        if server_info != None:
            print(f"Server {server_info.ipv4} ({server_info.ipv6}) already provisioned")
        else:
            print(f"Provisioning server...")
            server_info = server_provider.provision_server()
            print(f"Server {server_info.ipv4} ({server_info.ipv6}) successfully provisioned")

        self.config.render_ansible_vars()

        dns_provider = DnsProvider(self.config, server_info)
        dns_provider.render_dns_config()

        s = Server(server_info.ipv4)
        s.prepare_server_and_run_ansible()

        print(f"Server {server_info.ipv4} ({server_info.ipv6}) is now set up")

        print("Setting up DNS")
        s.run_dnscontrol()

        hostnames = dns_provider.get_hostnames()
        for hostname in hostnames:
            print(f"Waiting for DNS update for {hostname}")
            s.wait_for_dns(hostname)

        print(f"DNS record successfully updated")

        print(f"\n-----\n")
        print(f"ServeInfo:")
        print(f"  IPv4: {server_info.ipv4}")
        print(f"  IPv6: {server_info.ipv6}")
        print(f"")
        print(f"Deployed Web Apps:")
        for hostname in hostnames:
            print(f"  https://{hostname}")

    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())

        self.deploymentIdLineEdit = QLineEdit('')
        self.deploymentIdLineEdit.setReadOnly(True)
        self.deploymentIdLineEdit.textChanged.connect(self.config.set_uuid)
        deploymentIdLabel = QLabel("&Deployment ID:")
        deploymentIdLabel.setBuddy(self.deploymentIdLineEdit)
        deploymentIdButton = QPushButton("Regenerate")
        deploymentIdButton.clicked.connect(self.regenerateDeploymentId)

        deployButton = QPushButton("Deploy")
        deployButton.clicked.connect(self.onClick)

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
        providerComboBox.addItem("hetzner")
        providerComboBox.textActivated.connect(self.config.set_server_provider_type)

        providerLabel = QLabel("&Provider:")
        providerLabel.setBuddy(providerComboBox)

        apiTokenLineEdit = QLineEdit('')
        apiTokenLineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        apiTokenLineEdit.textChanged.connect(self.config.set_server_provider_api_key)
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
        providerComboBox.addItem("hetzner")
        providerComboBox.setEnabled(False)
        providerComboBox.textActivated.connect(self.config.set_dns_provider_type)
        providerLabel = QLabel("&Provider:")
        providerLabel.setBuddy(providerComboBox)

        apiTokenLineEdit = QLineEdit('')
        apiTokenLineEdit.setEchoMode(QLineEdit.EchoMode.Password)
        apiTokenLineEdit.setEnabled(False)
        apiTokenLineEdit.textChanged.connect(self.config.set_dns_provider_api_key)
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
        nameLineEdit.textChanged.connect(self.config.set_server_name)
        nameLabel = QLabel("&Name:")
        nameLabel.setBuddy(nameLineEdit)

        instanceComboBox = QComboBox()
        instanceComboBox.addItem("cx22")
        instanceComboBox.addItem("cx32")
        instanceComboBox.addItem("cx42")
        instanceComboBox.addItem("cx52")
        instanceComboBox.textActivated.connect(self.config.set_instance)
        instanceLabel = QLabel("&Instance Type:")
        instanceLabel.setBuddy(instanceComboBox)

        osComboBox = QComboBox()
        osComboBox.addItem("ubuntu")
        osComboBox.addItem("debian")
        osComboBox.textActivated.connect(self.config.set_image)
        osLabel = QLabel("&Operating System:")
        osLabel.setBuddy(osComboBox)

        sshKeyLineEdit = QLineEdit('')
        sshKeyLineEdit.textChanged.connect(self.config.set_ssh_pub_key)
        sshKeyLabel = QLabel("&SSH Key:")
        sshKeyLabel.setBuddy(sshKeyLineEdit)

        leMailLineEdit = QLineEdit('')
        leMailLineEdit.textChanged.connect(self.config.set_lets_encrypt_email)
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

    def configureWordpress(self, hostname):
        components = []
        components.append({
            "name": "watchtower",
            "type": "watchtower",
        })
        components.append({
            "name": "reverse-proxy",
            "type": "reverse-proxy",
        })
        components.append({
            "name": "wordpress",
            "type": "wordpress",
            "config": {
                "hostname": hostname,
            },
        })

        self.config.set_components(components)

    def createWordPressGroupBox(self):
        groupBox = QGroupBox("WordPress Settings")

        hostnameLineEdit = QLineEdit('')
        hostnameLineEdit.textChanged.connect(self.configureWordpress)
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
