const bookingSearch = document.getElementById("bookingSearch");
const enquirySearch = document.getElementById("enquirySearch");
const loungeSearch = document.getElementById("loungeSearch");
const agentSearch = document.getElementById("agentSearch");


if (enquirySearch) {
	const enquiryList = document.getElementById("enquiryList");

	enquirySearch.addEventListener("input", function () {
		const searchQuery = enquirySearch.value.toLowerCase().trim();

		// Filter items directly from enquiryList
		Array.from(enquiryList.getElementsByTagName("li")).forEach(item => {
			const enquiryText = item.textContent.toLowerCase();
			item.style.display = enquiryText.includes(searchQuery) ? "block" : "none";
		});
	});
}

if (loungeSearch) {
	const loungeList = document.getElementById("loungeList");

	loungeSearch.addEventListener("input", function () {
		const searchQuery = loungeSearch.value.toLowerCase().trim();

		// Filter items directly from loungeList
		Array.from(loungeList.getElementsByTagName("li")).forEach(item => {
			const loungeText = item.textContent.toLowerCase();
			item.style.display = loungeText.includes(searchQuery) ? "block" : "none";
		});
	});
}

if (agentSearch) {
	const agentList = document.getElementById("agentList");

	agentSearch.addEventListener("input", function () {
		const searchQuery = agentSearch.value.toLowerCase().trim();

		// Filter items directly from agentList
		Array.from(agentList.getElementsByTagName("li")).forEach(item => {
			const agentText = item.textContent.toLowerCase();
			item.style.display = agentText.includes(searchQuery) ? "block" : "none";
		});
	});
}

if (bookingSearch) {
	// Add your event listener or other functionality here
	bookingSearch.addEventListener("input", function () {
		const searchQuery = this.value.toLowerCase().trim();

	// Reset visibility
	document.querySelectorAll('.lounge-item, .booking-item').forEach(item => {
		item.style.display = "none";
	});

	// Search lounges
	document.querySelectorAll('.lounge-item').forEach(lounge => {
		const loungeText = lounge.textContent.toLowerCase();

		if (loungeText.includes(searchQuery)) {
			lounge.style.display = "block";

			// Show all bookings for this lounge
			const loungeId = lounge.getAttribute('data-lounge-id');
			document.querySelectorAll(`.booking-item[data-lounge-id="${loungeId}"]`).forEach(booking => {
				booking.style.display = "block";
			});
		}
	});

	// If no lounges match, search bookings
	if (!document.querySelector('.lounge-item[style*="display: block"]')) {
		document.querySelectorAll('.booking-item').forEach(booking => {
			const bookingText = booking.textContent.toLowerCase();

			if (bookingText.includes(searchQuery)) {
				booking.style.display = "block";

				// Show the parent lounge for this booking
				const loungeId = booking.getAttribute('data-lounge-id');
				document.querySelector(`.lounge-item[data-lounge-id="${loungeId}"]`).style.display = "block";
			}
		});
	}
	});
}

function closeAlert(button){
	var alert = button.parentElement;
	alert.style.display = 'none';
}

function displayMessage(message, category, message_div) {
	message_div.className = `flash-message ${category}`;
	message_div.innerText = message;
	message_div.style.display = "block";
	setTimeout(() => {
		message_div.style.display = "none";
	}, 5000); // Hide the message after 5 seconds
}

function clearFormFields() {
	document.getElementById("reset-password-form").reset();
}

function clearCookies() {
	document.cookie.split(";").forEach(function (c) {
		document.cookie =
			c.trim().split("=")[0] +
			"=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/";
	});
}

function showDiv(divId, ...focusInputNames) {
	var div = document.getElementById(divId);
	div.style.display = "block";
	focusInputNames.forEach((name) => {
		var input = document.querySelector(`input[name="${name}"]`);
		if (input) {
			input.setAttribute("required", true);
		}
	});
	var firstInput = document.querySelector(
		`input[name="${focusInputNames[0]}"]`,
	);
	if (firstInput) {
		setTimeout(() => firstInput.focus(), 100); // Delay to ensure visibility
	}
}