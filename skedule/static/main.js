(() => {
  feather.replace({width: '1em', height: '1em'})
})()

var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})

var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
  return new bootstrap.Popover(popoverTriggerEl)
})

function resizeXsBtns(){
  $('.btn-xs').each(function(i, obj) {
  if($(this).height() != parseInt($(this).css('line-height'))){
    $(this).css('line-height', '1');
  } else {
    $(this).css('line-height', '.5');
  }
  });
}
window.onresize = resizeXsBtns;
resizeXsBtns();

if(document.getElementById('endTime')){
  updateEndTime();
}

if(document.getElementById('templatesFormGroup')){
  loadTemplates();
}

function updateEndTime(){
  const startTime = document.getElementById('startTime').value
  const startDate = document.getElementById('startDate').value
  const duration = document.getElementById('duration').value
  
  const sHours = parseInt(startTime.slice(0,2));
  const sMins = parseInt(startTime.slice(2));
  const dHours = parseInt(duration.slice(0,2));
  const dMins = parseInt(duration.slice(2));

  
  var date = new Date(startDate);
  date.setTime(date.getTime()+ sHours*60*60*1000 + sMins*60*1000);
  date.setTime(date.getTime()+ dHours*60*60*1000 + dMins*60*1000);
  
  if(date.toString() != 'Invalid Date'){
    document.getElementById('endTime').value = Intl.DateTimeFormat('en-US', {month: '2-digit', day: '2-digit', year: 'numeric', hour:'2-digit', minute:'2-digit', hour12: false}).format(date).split(':').join('');
  } else {
    document.getElementById('endTime').value = '---';
  }
}

let isFormDirty = false;

function performExitConfirmation(){
    // Monitor form changes
    document.querySelectorAll("form input, form textarea, form select").forEach((element) => {
        element.addEventListener("input", () => {
            isFormDirty = true;
        });
    });

    // Add event listener for the beforeunload event
    window.addEventListener("beforeunload", (event) => {
        if (isFormDirty) {
            // Some browsers display this custom message; others show a generic one.
            event.preventDefault();
            event.returnValue = ""; // Required for the confirmation dialog to appear.
        }
    });

    document.querySelector("form").addEventListener("submit", () => {
      isFormDirty = false; // Prevent exit confirmation on successful submission
    });
}

const searchBar = document.getElementById("searchBar");
const searchSuggestions = document.getElementById("searchSuggestions");

// Helper function to format date in YYYY-MM-DD format with zero padding for URL
function formatDateWithPadding(date) {
    const year = date.getFullYear();
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // Zero-pad month
    const day = date.getDate().toString().padStart(2, '0'); // Zero-pad day
    return `${year}-${month}-${day}`; // Return formatted date in YYYY-MM-DD
}

// Helper function to format date without zero padding for suggestions
function formatDateWithoutPadding(month, day, year) {
    const formattedMonth = parseInt(month); // Remove zero padding from month
    const formattedDay = parseInt(day); // Remove zero padding from day
    return `${formattedMonth}/${formattedDay}/${year}`;
}

// Handle "input" event for autofill suggestions
searchBar.addEventListener("input", function (event) {
    const input = event.target.value.trim().toLowerCase(); // Normalize input
    searchSuggestions.innerHTML = ""; // Clear previous suggestions

    const todayKeyword = "Today";

    // Match "today" (case-insensitive and any variation starting with "t")
    if (input.length > 0 && todayKeyword.toLowerCase().startsWith(input.toLowerCase())) {

        // Add suggestion for today's date
        const suggestion = document.createElement("li");
        suggestion.textContent = todayKeyword;  // Display "today" as suggestion
        suggestion.className = "list-group-item list-group-item-action"; // Bootstrap classes
        suggestion.style.cursor = "pointer";
        searchSuggestions.appendChild(suggestion);
    }

    // Match month, day (optional), and year (optional) for date input
    const match = input.match(/^(\d{1,2})\/?(\d{0,2})?\/?(\d{0,4})$/); 
    if (match) {
        const month = match[1]; // Month (1-12)
        const dayPart = match[2] || ""; // Partial day (if any)
        const yearPart = match[3] || new Date().getFullYear(); // Use input year or default to current year

        // Ensure valid month (1-12)
        if (month >= 1 && month <= 12) {
            for (let day = 1; day <= 31; day++) {
                const dayStr = day.toString(); // No padding for day
                const fullDate = `${month}/${dayStr}/${yearPart}`;

                // Only suggest dates that match the partial input (month/day/year)
                if (dayPart && !fullDate.startsWith(`${month}/${dayPart}`)) {
                    continue;
                }

                // Add suggestion as a list item
                const suggestion = document.createElement("li");
                suggestion.textContent = formatDateWithoutPadding(month, dayStr, yearPart); // No zero-padding
                suggestion.className = "list-group-item list-group-item-action"; // Bootstrap classes
                suggestion.style.cursor = "pointer";

                searchSuggestions.appendChild(suggestion);
            }
        }
    }
});

// Handle suggestion click
searchSuggestions.addEventListener("click", function (event) {
    if (event.target.tagName === "LI") { // Ensure a list item was clicked
        const fullDate = event.target.textContent;
        searchBar.value = fullDate; // Set input value to the clicked suggestion
        searchSuggestions.innerHTML = ""; // Clear suggestions

        // Keep focus on the search bar after selection
        searchBar.focus();
    }
});

let selectedSuggestion = -1;

// Handle "Enter" key event to redirect when "today" or any valid date is typed
searchBar.addEventListener("keydown", function (event) {
    const suggestions = Array.from(searchSuggestions.querySelectorAll("li"));

    if (event.key === "Enter") {
        const input = searchBar.value.trim().toLowerCase();

        // Check if input is "today"
        if (input === "today") {
            const today = new Date();
            const todayDate = formatDateWithPadding(today); // Get today's date in YYYY-MM-DD format
            window.location.href = `/schedule?week=${todayDate}`; // Redirect to today's URL with zero-padded date in the correct format
        }
        // Check if the input matches a date format (MM/DD/YYYY)
        else {
            const match = input.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/); // MM/DD/YYYY
            if (match) {
                const month = match[1];
                const day = match[2];
                const year = match[3];
                const formattedDate = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`; // Format to YYYY-MM-DD
                window.location.href = `/schedule?week=${formattedDate}`; // Redirect to formatted URL
            }
        }
    }
    // Handle "Tab" key to autofill the first suggestion
    if (event.key === "Tab") {
        event.preventDefault(); // Prevent default tab behavior

        if (suggestions.length > 0) {
            // Increment selectedSuggestion to go down the list
            selectedSuggestion = (selectedSuggestion + 1) % suggestions.length;

            // Highlight the current suggestion
            suggestions.forEach((suggestion, index) => {
                if (index === selectedSuggestion) {
                    suggestion.classList.add("active"); // Add a class for styling the active suggestion
                    searchBar.value = suggestion.textContent; // Autofill the search bar with the current suggestion
                } else {
                    suggestion.classList.remove("active"); // Remove the active class from others
                }
            });
        }
    }
});

// Hide suggestions when input loses focus
searchBar.addEventListener("blur", function () {
    setTimeout(() => (searchSuggestions.innerHTML = ""), 200); // Delay to allow click on suggestion
});

document.addEventListener("keydown", function (event) {
    // Check if the pressed key is `/` and no input or textarea is focused
    if (event.key === "/" && !event.target.matches("input, textarea")) {
        event.preventDefault(); // Prevent default behavior (e.g., quick find in some browsers)
        
        // Focus or open the search bar
        if (searchBar) {
            searchBar.focus();
        }
    }
});