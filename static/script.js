function generateSpeech() {
    const textArea = document.getElementById("textToSpeak");
    const textValue = textArea.value.trim();
    if (!textValue) {
      alert("Please enter some text.");
      return;
    }
    // 임시 시연
    alert("Generate speech clicked!\nYour text:\n" + textValue);
  }