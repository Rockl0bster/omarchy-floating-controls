import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import qs.Commons as Commons

Panel {
  id: root
  moduleName: "io.github.rockl0bster.floating-controls"
  ipcTarget: moduleName
  property string feedback: ""
  property bool installed: false
  property string selectedMode: "both"
  readonly property string manager: decodeURIComponent(Qt.resolvedUrl("manage.py").toString().replace(/^file:\/\//, ""))

  Commons.Translations { id: strings; directory: Qt.resolvedUrl("i18n") }

  function run(action) {
    if (operation.running) return
    feedback = ""
    operation.command = ["python3", manager, action]
    if (action === "install") operation.command = ["python3", manager, action, "--mode", selectedMode]
    operation.running = true
  }
  function refresh() {
    if (!status.running) status.running = true
  }
  Component.onCompleted: refresh()
  onOpenedChanged: if (opened) refresh()

  Process {
    id: status
    command: ["python3", root.manager, "status", "--json"]
    stdout: StdioCollector {
      onStreamFinished: {
        try {
          var state = JSON.parse(text)
          root.installed = state.installed === true
          root.selectedMode = state.mode
        } catch (error) { root.feedback = strings.t("failed") }
      }
    }
  }
  Process {
    id: operation
    property string output: ""
    stdout: StdioCollector { onStreamFinished: operation.output = text }
    stderr: StdioCollector { onStreamFinished: if (text.trim()) operation.output = text }
    onStarted: output = ""
    onExited: function(code) {
      root.feedback = code === 0 ? strings.t("done") : strings.t("failed") + " " + output.trim()
      root.refresh()
    }
  }

  BarIconButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: "󰖲"
    tooltipText: strings.t("title")
    onPressed: function(b) { root.toggle() }
  }
  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  KeyboardPanel {
    id: panel
    anchorItem: button
    owner: root
    bar: root.bar
    open: root.opened
    focusTarget: keys
    contentWidth: panel.fittedContentWidth(Style.space(340))
    contentHeight: panel.fittedContentHeight(column.implicitHeight)
    PanelKeyCatcher {
      id: keys
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }
      Column {
        id: column
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        spacing: Style.space(12)
        PanelSectionHeader { text: strings.t("title"); foreground: root.bar.foreground; fontFamily: root.bar.fontFamily }
        Text {
          width: parent.width
          textFormat: Text.PlainText
          wrapMode: Text.WordWrap
          color: root.bar.foreground
          font.family: root.bar.fontFamily
          text: strings.t("explanation")
        }
        Text {
          width: parent.width
          textFormat: Text.PlainText
          wrapMode: Text.WordWrap
          color: root.bar.foreground
          font.family: root.bar.fontFamily
          text: root.installed ? strings.t("active") : strings.t("inactive")
        }
        Text {
          width: parent.width
          textFormat: Text.PlainText
          wrapMode: Text.Wrap
          color: root.bar.foreground
          font.family: root.bar.fontFamily
          text: strings.t("preview")
        }
        Image {
          anchors.horizontalCenter: parent.horizontalCenter
          width: Math.min(parent.width, implicitWidth)
          height: 33
          fillMode: Image.PreserveAspectFit
          asynchronous: false
          source: Qt.resolvedUrl("previews/" + (root.selectedMode === "workspace" ? "workspace"
            : root.selectedMode === "halves" ? "halves" : root.selectedMode === "none" ? "none" : "both") + ".png")
        }
        Button {
          width: parent.width
          text: strings.t("mode_both")
          selected: root.selectedMode === "both"
          foreground: root.bar.foreground
          enabled: !operation.running
          onClicked: root.selectedMode = "both"
        }
        Button {
          width: parent.width
          text: strings.t("mode_workspace")
          selected: root.selectedMode === "workspace"
          foreground: root.bar.foreground
          enabled: !operation.running
          onClicked: root.selectedMode = "workspace"
        }
        Button {
          width: parent.width
          text: strings.t("mode_halves")
          selected: root.selectedMode === "halves"
          foreground: root.bar.foreground
          enabled: !operation.running
          onClicked: root.selectedMode = "halves"
        }
        Button {
          width: parent.width
          text: strings.t("mode_none")
          selected: root.selectedMode === "none"
          foreground: root.bar.foreground
          enabled: !operation.running
          onClicked: root.selectedMode = "none"
        }
        Button {
          width: parent.width
          text: root.installed ? strings.t("apply") : strings.t("install")
          foreground: root.bar.foreground
          enabled: !operation.running
          onClicked: root.run("install")
        }
        Button {
          width: parent.width
          visible: root.installed
          text: strings.t("remove")
          foreground: root.bar.foreground
          enabled: !operation.running
          onClicked: root.run("uninstall")
        }
        Text {
          width: parent.width
          visible: root.feedback !== ""
          textFormat: Text.PlainText
          wrapMode: Text.WordWrap
          color: root.bar.foreground
          font.family: root.bar.fontFamily
          text: root.feedback
        }
      }
    }
  }
}
