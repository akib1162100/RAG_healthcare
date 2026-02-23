document.addEventListener("DOMContentLoaded", function () {
    // === ELEMENTS ===
    const sendOtpBtn = document.getElementById('send_otp_btn');
    const verifyOtpBtn = document.getElementById('verify_otp_btn');
    const otpInputContainer = document.querySelector('#otp_input_container');
    const phoneInput = document.querySelector('input[name="phone"]');
    const otpInput = document.getElementById('otp_input');
    const signupBtn = document.getElementById('signup_btn');
    const countrySelect = document.querySelector('select[name="country_id"]');
    const stateSelect = document.querySelector('select[name="state_id"]');
    const phoneCodeSelect = document.querySelector('select[name="phone_code"]');

    console.log("=== Script Initialized ===");

    // === COUNTRY–STATE FILTERING & PHONE CODE AUTO-FILL ===
    if (countrySelect && stateSelect) {
        console.log("Country-State Select Found");

        // Store all states initially
        const allStates = Array.from(stateSelect.options);
        console.log("Total States Loaded:", allStates.length);

        // Hide state dropdown initially until country is selected
        stateSelect.closest('.form-group').style.display = 'none';

        countrySelect.addEventListener('change', function () {
            const selectedCountryId = this.value;
            const selectedOption = this.options[this.selectedIndex];
            const phoneCode = selectedOption.getAttribute('data-phone-code');


            console.log("Selected Country:", selectedCountryId);
            console.log("Phone Code from data attribute:", phoneCode);

            // *** AUTO-FILL PHONE CODE ***
            if (phoneCodeSelect && phoneCode) {
                // Set the phone code select to match the country's phone code
                for (let i = 0; i < phoneCodeSelect.options.length; i++) {
                    if (String(phoneCodeSelect.options[i].value) === String(phoneCode)) {
    phoneCodeSelect.selectedIndex = i;
}

                }
            }

            // Clear existing options and reset to placeholder
            stateSelect.innerHTML = '<option value="">Select State</option>';

            if (selectedCountryId) {
                // Filter states by country ID
                allStates.forEach(option => {
                    if (option.dataset.countryId === selectedCountryId) {
                        stateSelect.appendChild(option.cloneNode(true));
                    }
                });

                // Show state dropdown if any states are available
                if (stateSelect.options.length > 1) {
                    stateSelect.closest('.form-group').style.display = 'block';
                } else {
                    stateSelect.closest('.form-group').style.display = 'none';
                }
            } else {
                // Hide again if no country selected
                stateSelect.closest('.form-group').style.display = 'none';
                // Clear phone code if no country selected
                if (phoneCodeSelect) {
                    phoneCodeSelect.selectedIndex = 0;
                }
            }

            console.log("States Available After Filter:", stateSelect.options.length);
        });
    } else {
        console.error("Country or State select element not found!");
    }

    // === SEND OTP ===
    if (sendOtpBtn) {
        sendOtpBtn.addEventListener('click', async function () {
            console.log('Send OTP button clicked');
            const phoneCode = phoneCodeSelect ? phoneCodeSelect.value.trim() : "";
            const phone = phoneInput ? phoneInput.value.trim() : "";
            if (phone.startsWith('0')) {
        alert("Phone number must not start with 0");
        phoneInput.focus();
        return;
    }

            // Combine phone code with phone number for OTP
            const fullPhone = phoneCode && phone ? `+${phoneCode} ${phone}` : phone;

            if (!phone) {
                alert("Please enter your phone number.");
                return;
            }

            if (!phoneCode) {
                alert("Please select a country code.");
                return;
            }

            try {
                const response = await fetch('/send/otp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: { phone: fullPhone },
                        id: Date.now()
                    })
                });

                const result = await response.json();
                const payload = result.result;
                console.log("Send OTP Result:", result);

                if (payload && payload.success) {
                    alert(payload.message);
                    if (otpInputContainer) otpInputContainer.style.display = 'block';
                    if (verifyOtpBtn) verifyOtpBtn.style.display = 'block';
                    sendOtpBtn.style.display = 'none';
                } else {
                    alert(payload ? payload.error : "Something went wrong while sending OTP.");
                }
            } catch (err) {
                console.error("Error (Send OTP):", err);
                alert("Something went wrong while sending OTP.");
            }
        });
    }

    // === VERIFY OTP ===
    if (verifyOtpBtn) {
        verifyOtpBtn.addEventListener('click', async function () {
            console.log('Verify OTP button clicked');
            const phoneCode = phoneCodeSelect ? phoneCodeSelect.value.trim() : "";
            const phone = phoneInput ? phoneInput.value.trim() : "";
            const otp = otpInput ? otpInput.value.trim() : "";

            // Combine phone code with phone number for verification
            const fullPhone = phoneCode && phone ? `+${phoneCode} ${phone}` : phone;

            if (!otp) {
                alert("Please enter the OTP.");
                return;
            }

            try {
                const response = await fetch('/verify/otp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        jsonrpc: "2.0",
                        method: "call",
                        params: { phone: fullPhone, otp: otp },
                        id: Date.now()
                    })
                });

                const result = await response.json();
                const payload = result.result;
                console.log("Verify OTP Result:", result);

                if (payload && payload.success) {
                    alert(payload.message);
                    if (otpInputContainer) otpInputContainer.style.display = 'none';
                    if (verifyOtpBtn) verifyOtpBtn.style.display = 'none';
                    if (signupBtn) signupBtn.style.display = 'block';
                    verifyOtpBtn.disabled = true;
                } else {
                    alert(payload ? payload.error : "Something went wrong while verifying OTP.");
                }
            } catch (err) {
                console.error("Error (Verify OTP):", err);
                alert("Something went wrong while verifying OTP.");
            }
        });
    }
});