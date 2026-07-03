document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('predictionForm');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');
    
    const contentGrid = document.querySelector('.content-grid');
    const resultCard = document.getElementById('resultCard');
    const resultOutcome = document.getElementById('resultOutcome');
    const confidenceValue = document.getElementById('confidenceValue');
    const progressBarFill = document.getElementById('progressBarFill');
    const resultDetails = document.getElementById('resultDetails');
    const resetBtn = document.getElementById('resetBtn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Loading State
        submitBtn.disabled = true;
        btnText.textContent = 'Running Evaluation...';
        spinner.classList.remove('hidden');
        resultCard.classList.add('hidden');
        contentGrid.classList.remove('has-result');

        // Extract Form Data
        const formData = new FormData(form);
        const payload = {};
        formData.forEach((value, key) => {
            payload[key] = value;
        });

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (response.status === 401) {
                alert('Session expired or unauthorized. Redirecting to login page...');
                window.location.href = '/login';
                return;
            }

            const result = await response.json();

            if (result.success) {
                // Show Result Panel
                resultCard.classList.remove('hidden');
                contentGrid.classList.add('has-result');

                // Determine outcome UI components
                const isApproved = result.prediction === 1;
                const statusClass = isApproved ? 'approved' : 'denied';
                const statusLabel = isApproved ? 'Approved' : 'Denied';
                const statusTitle = isApproved ? 'Application Approved' : 'Application Rejected';
                
                // Inject Outcome Status
                resultOutcome.innerHTML = `
                    <span class="status-badge ${statusClass}">${statusLabel}</span>
                    <h1 class="outcome-title ${statusClass}">${statusTitle}</h1>
                `;

                // Update Confidence Score and progress bar
                const confidencePct = Math.round(result.confidence * 100);
                confidenceValue.textContent = `${confidencePct}%`;
                confidenceValue.className = `confidence-value ${statusClass}`;
                progressBarFill.style.width = `${confidencePct}%`;
                
                // Progress Bar Color change based on outcome
                if (isApproved) {
                    progressBarFill.style.background = 'linear-gradient(90deg, #10b981 0%, #059669 100%)';
                } else {
                    progressBarFill.style.background = 'linear-gradient(90deg, #f43f5e 0%, #e11d48 100%)';
                }

                // Inject Details Text
                const loanAmt = parseFloat(payload['LoanAmount']);
                const formattedLoanAmt = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(loanAmt);
                
                let detailsHtml = '';
                if (isApproved) {
                    detailsHtml = `
                        <p>The automated risk assessment engine has processed the inputs. 
                        With a prediction confidence of <span class="detail-highlight">${confidencePct}%</span>, 
                        the requested loan amount of <span class="detail-highlight">${formattedLoanAmt}</span> 
                        for a term of <span class="detail-highlight">${payload['Loan_Amount_Term']} years</span> is 
                        <span class="detail-highlight" style="color: var(--success-color);">Approved</span>. 
                        The applicant's financial profile, particularly credit history, conforms to the target threshold.</p>
                    `;
                } else {
                    let rejectMsg = '';
                    if (result.dti_overridden) {
                        const formattedEmi = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(result.emi);
                        const formattedIncome = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(parseFloat(payload['ApplicantIncome']) + parseFloat(payload['CoapplicantIncome']));
                        rejectMsg = `The application has been <span class="detail-highlight" style="color: var(--error-color);">Rejected</span> due to standard debt-to-income regulations. The estimated monthly EMI of <span class="detail-highlight">${formattedEmi}</span> exceeds 55% of the applicant's combined monthly income of <span class="detail-highlight">${formattedIncome}</span>.`;
                    } else {
                        rejectMsg = `The automated risk assessment engine has flagged this request as high risk. With a prediction confidence of <span class="detail-highlight">${confidencePct}%</span>, the requested loan of <span class="detail-highlight">${formattedLoanAmt}</span> has been <span class="detail-highlight" style="color: var(--error-color);">Rejected</span>. Key risk contributors include the applicant's credit history status or insufficient debt-to-income capacity relative to the loan size.`;
                    }
                    detailsHtml = `<p>${rejectMsg}</p>`;
                }
                resultDetails.innerHTML = detailsHtml;

                // Smooth Scroll to Result Card
                resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

            } else {
                alert(`Error: ${result.error || 'An error occurred during prediction'}`);
            }

        } catch (error) {
            console.error('Fetch error:', error);
            alert('A system error occurred. Please verify backend connection and try again.');
        } finally {
            // Restore Submit Button State
            submitBtn.disabled = false;
            btnText.textContent = 'Analyze Application';
            spinner.classList.add('hidden');
        }
    });

    // Reset UI Handler
    resetBtn.addEventListener('click', () => {
        form.reset();
        resultCard.classList.add('hidden');
        contentGrid.classList.remove('has-result');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});
