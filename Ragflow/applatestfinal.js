class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
        };

        this.state = false;
        this.messages = [];
        this.inactivityTimer = null;
        this.inactivityPromptDisplayed = false;
        this.args.voiceInputButton = document.querySelector('.voice-input-button');
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.sessionId = this.getSessionId();

        this.startInactivityTimer();
    }

    getSessionId() {
        let sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now();
            localStorage.setItem('chatSessionId', sessionId)
        }
        return sessionId;
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
            this.resetInactivityTimer();  // Reset the timer on typing
        });

        this.args.voiceInputButton.addEventListener('click', () => this.toggleVoiceInput());

        // Reset inactivity timer on any chatbox click or interaction
        chatBox.addEventListener('click', () => this.resetInactivityTimer());
        sendButton.addEventListener('click', () => this.resetInactivityTimer());
    }

    toggleState(chatbox) {
        this.state = !this.state;

        // Show or hide the chatbox
        if (this.state) {
            chatbox.classList.add('chatbox--active');
            this.resetInactivityTimer();
        } else {
            chatbox.classList.remove('chatbox--active');
            this.clearInactivityTimer();
        }
    }

    onSendButton(chatbox) {
        const textField = chatbox.querySelector('input');
        const text1 = textField.value.trim();
        if (text1 === "") return;

        let msg1 = { name: "User", message: text1 };
        this.messages.push(msg1);

        this.updateChatText(chatbox);
        textField.value = '';
        this.sendMessage(text1);
    }

    sendMessage(message) {
        const chatHistory = this.messages.map(msg => ({
            role: msg.name === "User" ? "user" : "assistant",
            content: msg.message
        }));

        fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sessionId: this.sessionId,
                question: message,
                chat_history: chatHistory
            }),
        })
        .then(response => response.json())
        .then(data => {
            let botMessage = { name: "CloudJune", message: data.result };
            this.messages.push(botMessage);

            // Handle key points if needed
            if (data.key_points) {
                console.log("Key points:", data.key_points);
            }

            // Reset inactivity timer since the bot has replied
            this.resetInactivityTimer();

            // Update the chat UI
            this.updateChatText(this.args.chatBox);
        })
        .catch(error => {
            console.error('Error:', error);
            let errorMessage = { name: "CloudJune", message: "Sorry, something went wrong." };
            this.messages.push(errorMessage);

            // Reset inactivity timer on error
            this.resetInactivityTimer();

            this.updateChatText(this.args.chatBox);
        });
    }

    toggleVoiceInput() {
        if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
            this.mediaRecorder.stop();
            this.args.voiceInputButton.innerHTML = '<i class="fas fa-microphone"></i>';
        } else {
            navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.mediaRecorder = new MediaRecorder(stream);
                this.mediaRecorder.ondataavailable = (event) => {
                    this.audioChunks.push(event.data);
                };
                this.mediaRecorder.onstop = () => {
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                    this.sendAudioToServer(audioBlob);
                    this.audioChunks = [];
                };
                this.mediaRecorder.start();
                this.args.voiceInputButton.innerHTML = '<i class="fas fa-stop"></i>';
            })
            .catch(error => console.error('Error accessing microphone:', error));
        }
    }

    sendAudioToServer(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob);

        fetch('/speech-to-text', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Speech-to-text request failed');
            }
            return response.json();
        })
        .then(data => {
            if (data.text) {
                this.args.chatBox.querySelector('input').value = data.text;
                this.onSendButton(this.args.chatBox);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to convert speech to text. Please try again.');
        });
    }

    updateChatText(chatbox) {
        let html = '';
        this.messages.slice().reverse().forEach(function(item) {
            if (item.name === "CloudJune") {
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>';
            } else {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>';
            }
        });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
        this.addTextToSpeechButtons();
    }

    addTextToSpeechButtons() {
        const botMessages = document.querySelectorAll('.messages__item--visitor');
        botMessages.forEach(message => {
            if (!message.querySelector('.text-to-speech-button')) {
                const button = document.createElement('button');
                button.className = 'text-to-speech-button';
                button.innerHTML = '<i class="fas fa-volume-up"></i>';
                button.addEventListener('click', () => {
                    const textToSpeak = message.textContent.replace(button.textContent, '').trim();
                    console.log("Text extracted for TTS:", textToSpeak);
                    this.textToSpeech(textToSpeak) // Debugging line
                });
                message.appendChild(button);
            }
        });
    }

    textToSpeech(text) {
        console.log("Text being send for TTS:". text); // Debugging line
        fetch('/text-to-speech', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: text })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Text-to-speech request failed');
            }
            return response.blob();
        })
        .then(blob => {
            if (blob.size === 0) {
                throw new Error('Recieved empty audio data');
            }
            const audio = new Audio(URL.createObjectURL(blob));
            audio.play();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Failed to convert text to speech. Please try again.');
        });
    }

    startInactivityTimer() {
        this.inactivityTimer = setTimeout(() => {
            if (!this.inactivityPromptDisplayed) {
                this.showInactivityPrompt();
            }
        }, 180000);  // 3 minutes
    }

    resetInactivityTimer() {
        clearTimeout(this.inactivityTimer);  // Clear existing timer
        this.inactivityPromptDisplayed = false;
        this.startInactivityTimer();  // Start a new inactivity timer
    }

    clearInactivityTimer() {
        clearTimeout(this.inactivityTimer);
    }

    showInactivityPrompt() {
        this.inactivityPromptDisplayed = true;
        if (confirm("Do you want to continue the chat?")) {
            this.resetInactivityTimer();
        } else {
            this.terminateSession();
        }
    }

    terminateSession() {
        this.clearInactivityTimer();
        const chatbox = this.args.chatBox;
        let msg = { name: "CloudJune", message: "Bye! Have a great day." };
        this.messages.push(msg);
        this.updateChatText(chatbox);
        chatbox.classList.remove('chatbox--active');
    }
}

const chatbox = new Chatbox();
chatbox.display();