class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.messages = [];
    }

    display() {
        const { openButton, chatBox, sendButton } = this.args;
        openButton.addEventListener('click', () => this.toggleState(chatBox));
        sendButton.addEventListener('click', () => this.onSendButton(chatBox));

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox);
            }
        });
    }

    toggleState(chatbox) {
        this.state = !this.state;

        // show or hides the box
        if (this.state) {
            chatbox.classList.add('chatbox--active');
        } else {
            chatbox.classList.remove('chatbox--active');
        }
    }

    onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value;
        if (text1 === "") {
            return;
        }

        textField.value = "";  // Clear the input field after sending the message

        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);

        let typingMessage = { name: "CLoudjune", message: "Typing..." };
        this.messages.push(typingMessage);
        this.updateChatText(chatbox);

        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: text1,          // Send the user's input
                chat_history: this.messages  // Send the chat history
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove "Typing..." message
            this.messages.pop();

            // Add bot's response to the messages array
            let botMessage = { name: "CLoudjune", message: data.result };  // Update UI with the bot's response
            this.messages.push(botMessage);

            // Update the chat UI
            this.updateChatText(chatbox);
        })
        .catch(error => {
            console.error('Error:', error);

            // Remove "Typing..." message
            this.messages.pop();
            let errorMessage = { name: "CLoudjune", message: "Sorry, something went wrong." };
            this.messages.push(errorMessage);
            this.updateChatText(chatbox);
        });
    }

    updateChatText(chatbox) {
        var html = '';
        this.messages.slice().reverse().forEach(function(item) {
            if (item.name === "CLoudjune") {
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>';
            } else {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>';
            }
        });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }
}

const chatbox = new Chatbox();
chatbox.display();
