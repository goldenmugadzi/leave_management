window.addEventListener("DOMContentLoaded", () => {
    console.log('dom content loaded')
    let calcButton = document.getElementById("calculate_button");
    let amount = document.getElementById("id_amount");
    amount.addEventListener("change", () => {
        console.log("clicked");
        if (document.getElementById("id_amount").value && document.getElementById("id_budget_id").value) {
            let amount = document.getElementById("id_amount").value
            let budget_id = document.getElementById("id_budget_id").value
            console.log(amount, budget_id)
            // make budget id integer
            budget_id = parseInt(budget_id)
            console.log(amount, budget_id)
            fetch(`/ace/balance/${budget_id}`).then(r =>
            r.json().then(data => {
                console.log(data)

                document.getElementById("modal-body-content").innerHTML = data
                const currentBalance = data.balance;
                const budgetName = data.name;
                const withdrawnAmount = data.withdrawn;

                // Calculate remaining balance
                const remainingBalance = currentBalance - amount;
                const modalBody = document.getElementById('modal-body-content');

                // Update modal content
                modalBody.textContent = `The remaining balance after this transaction would be: ZIG ${remainingBalance} The amount already withdrawn from the ${budgetName} budget is: $${withdrawnAmount}`;

                // Show modal
                $('#resultModal').modal('show');
            }))
        }
    })
    });