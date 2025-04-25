const submitButton = document.getElementById("submitEnquiry");
const messageTextarea = document.getElementById("message");
const message = document.getElementById('message');
const char_count = document.getElementById('char_count');
const topicDropdown = document.getElementById("topic");
const postcodeContainer = document.getElementById('postcode-container');

if (postcodeContainer) {
	fetch('/static/suburbs.json')
	.then(response => response.json())
	.then(data => {
		const postcodeField = document.getElementById('postcode');
		const stateContainer = document.getElementById('state-container');
		const localityContainer = document.getElementById('locality-container');
		const stateField = document.getElementById('state');
		const localitySelect = document.getElementById('locality');

		if (postcodeField) {
			postcodeField.addEventListener('input', function () {
				const postcode = this.value.trim(); // Get and trim the entered postcode
				localitySelect.innerHTML = '<option value="">Select Suburb</option>'; // Reset options
				stateField.value = ''; // Clear state field
				stateContainer.style.display = 'none'; // Hide state container by default
				localityContainer.style.display = 'none'; // Hide locality container by default

				const filteredLocalities = data.filter(entry => entry.postcode === postcode);

				if (filteredLocalities.length > 0) {
					stateField.value = filteredLocalities[0].state; // Set state value
					stateContainer.style.display = 'flex'; // Show state container
					localityContainer.style.display = 'flex'; // Show locality container

					filteredLocalities.forEach(entry => {
						const option = document.createElement('option');
						option.value = entry.locality;
						option.text = entry.locality;
						localitySelect.appendChild(option); // Append each locality option
					});
				}
			});
		}
	})
	.catch(error => console.error('Error fetching suburb data:', error));
}

if (submitButton && messageTextarea) {
	let profaneWords = [];
	
	fetch('/static/profanity_wordlist.txt')
	.then(response => {
		return response.text();
	})
	.then(data => {
		profaneWords = data.split("\n").map(word => word.trim());
	})
	.catch(error => console.error("Error fetching profanity list:", error));

	messageTextarea.addEventListener("input", function () {
		const messageContent = messageTextarea.value.toLowerCase(); // Normalize input to lowercase
		let containsProfanity = false;

		// Check for profanity (single words and phrases)
		profaneWords.forEach(word => {
			if (word) { // Ensure the word is not empty
				const regex = new RegExp(`\\b${word}\\b`, 'i'); // Match whole words/phrases
				if (regex.test(messageContent)) {
					containsProfanity = true;
				}
			}
		});

		// Disable or enable the submit button based on profanity detection
		if (containsProfanity) {
			submitButton.disabled = true; // Disable the button
			submitButton.style.backgroundColor = "gray"; // Optional: Visual cue
		} else {
			submitButton.disabled = false; // Enable the button
			submitButton.style.backgroundColor = ""; // Reset visual cue
		}
	});
}

if (message && char_count) {
	message.addEventListener('input', function() {
	  const current_length = message.value.length;
	  char_count.textContent = `${current_length} / 2000`;
	});
}

if (topicDropdown && messageTextarea) {
	const loungeAddress = topicDropdown.getAttribute("data-lounge-address");

	topicDropdown.addEventListener("change", function () {
		if (topicDropdown.value === "lounge_enquiry" && loungeAddress) {
			const prefix = `Message regarding Lounge: ${loungeAddress}\n\n`;
			messageTextarea.value = prefix;

			messageTextarea.addEventListener("input", function () {
				if (!messageTextarea.value.startsWith(prefix)) {
					messageTextarea.value = prefix;
				}
			});
		} else {
			messageTextarea.value = "";
			messageTextarea.removeEventListener("input", arguments.callee);
		}
	});
}