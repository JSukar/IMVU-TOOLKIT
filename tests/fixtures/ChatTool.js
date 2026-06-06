function appendMessage(messageNode, msg) {
    $(messageNode).append(IMVU.Client.util.linkify(msg));
}
