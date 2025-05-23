import { Chart } from "@/components/ui/chart"
document.addEventListener("DOMContentLoaded", () => {
  // Initialize charts if they exist
  initFinancialChart()
  initCustomerChart()

  // Initialize dashboard stats animation
  animateStats()

  // Initialize dashboard refresh
  initDashboardRefresh()
})

// Financial chart
function initFinancialChart() {
  const financialChartEl = document.getElementById("financialChart")

  if (financialChartEl) {
    const ctx = financialChartEl.getContext("2d")

    // Get data from the element's data attributes
    const labels = JSON.parse(financialChartEl.getAttribute("data-labels") || "[]")
    const incomeData = JSON.parse(financialChartEl.getAttribute("data-income") || "[]")
    const expenseData = JSON.parse(financialChartEl.getAttribute("data-expense") || "[]")

    // Format labels to be more readable (e.g., "Jan 2023")
    const formattedLabels = labels.map((label) => {
      const [year, month] = label.split("-")
      const date = new Date(year, month - 1)
      return date.toLocaleDateString("en-US", { month: "short", year: "numeric" })
    })

    // Create chart
    const financialChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: formattedLabels,
        datasets: [
          {
            label: "Income",
            data: incomeData,
            backgroundColor: "rgba(40, 205, 65, 0.7)",
            borderColor: "rgba(40, 205, 65, 1)",
            borderWidth: 1,
          },
          {
            label: "Expenses",
            data: expenseData,
            backgroundColor: "rgba(255, 59, 48, 0.7)",
            borderColor: "rgba(255, 59, 48, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              usePointStyle: true,
              padding: 20,
              font: {
                size: 12,
              },
            },
          },
          tooltip: {
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            titleColor: "#1d1d1f",
            bodyColor: "#1d1d1f",
            borderColor: "rgba(210, 210, 215, 0.5)",
            borderWidth: 1,
            cornerRadius: 8,
            padding: 12,
            boxPadding: 6,
            usePointStyle: true,
            callbacks: {
              label: (context) => {
                let label = context.dataset.label || ""
                if (label) {
                  label += ": "
                }
                if (context.parsed.y !== null) {
                  label += new Intl.NumberFormat("en-PK", {
                    style: "currency",
                    currency: "PKR",
                    minimumFractionDigits: 0,
                  }).format(context.parsed.y)
                }
                return label
              },
            },
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
          },
          y: {
            beginAtZero: true,
            ticks: {
              callback: (value) =>
                new Intl.NumberFormat("en-PK", {
                  style: "currency",
                  currency: "PKR",
                  notation: "compact",
                  minimumFractionDigits: 0,
                }).format(value),
            },
          },
        },
      },
    })
  }
}

// Customer chart
function initCustomerChart() {
  const customerChartEl = document.getElementById("customerChart")

  if (customerChartEl) {
    const ctx = customerChartEl.getContext("2d")

    // Get data from the element's data attributes
    const labels = JSON.parse(customerChartEl.getAttribute("data-labels") || "[]")
    const data = JSON.parse(customerChartEl.getAttribute("data-values") || "[]")

    // Create chart
    const customerChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "New Customers",
            data: data,
            backgroundColor: "rgba(0, 113, 227, 0.1)",
            borderColor: "rgba(0, 113, 227, 1)",
            borderWidth: 2,
            pointBackgroundColor: "rgba(0, 113, 227, 1)",
            pointBorderColor: "#fff",
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: true,
            tension: 0.4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: "rgba(255, 255, 255, 0.9)",
            titleColor: "#1d1d1f",
            bodyColor: "#1d1d1f",
            borderColor: "rgba(210, 210, 215, 0.5)",
            borderWidth: 1,
            cornerRadius: 8,
            padding: 12,
            boxPadding: 6,
          },
        },
        scales: {
          x: {
            grid: {
              display: false,
            },
          },
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
            },
          },
        },
      },
    })
  }
}

// Animate stats
function animateStats() {
  document.querySelectorAll(".stats-card-value").forEach((element) => {
    const finalValue = Number.parseFloat(element.getAttribute("data-value") || "0")
    const prefix = element.getAttribute("data-prefix") || ""
    const suffix = element.getAttribute("data-suffix") || ""
    const duration = 1500 // Animation duration in milliseconds
    const frameDuration = 1000 / 60 // 60fps
    const totalFrames = Math.round(duration / frameDuration)
    let frame = 0

    // Start with 0
    element.textContent = prefix + "0" + suffix

    // Animate to final value
    const counter = setInterval(() => {
      frame++

      const progress = frame / totalFrames
      const currentValue = Math.round(finalValue * progress)

      element.textContent = prefix + currentValue.toLocaleString() + suffix

      if (frame === totalFrames) {
        clearInterval(counter)
      }
    }, frameDuration)
  })
}

// Dashboard refresh
function initDashboardRefresh() {
  const refreshButton = document.getElementById("refreshDashboard")

  if (refreshButton) {
    refreshButton.addEventListener("click", function () {
      this.classList.add("rotating")

      // Fetch updated dashboard data
      fetch("/api/dashboard/summary")
        .then((response) => response.json())
        .then((data) => {
          // Update stats
          document.getElementById("totalCustomers").textContent = data.total_customers
          document.getElementById("totalProducts").textContent = data.total_products
          document.getElementById("totalEarnings").textContent = formatCurrency(data.total_earnings)
          document.getElementById("totalExpenditures").textContent = formatCurrency(data.total_expenditures)
          document.getElementById("netBalance").textContent = formatCurrency(data.net_balance)

          // Show success message
          const toast = document.createElement("div")
          toast.className = "toast toast-success"
          toast.innerHTML = '<i class="fas fa-check-circle"></i> Dashboard refreshed successfully'
          document.body.appendChild(toast)

          setTimeout(() => {
            toast.classList.add("show")
          }, 100)

          setTimeout(() => {
            toast.classList.remove("show")
            setTimeout(() => {
              toast.remove()
            }, 300)
          }, 3000)
        })
        .catch((error) => {
          console.error("Error refreshing dashboard:", error)

          // Show error message
          const toast = document.createElement("div")
          toast.className = "toast toast-error"
          toast.innerHTML = '<i class="fas fa-exclamation-circle"></i> Failed to refresh dashboard'
          document.body.appendChild(toast)

          setTimeout(() => {
            toast.classList.add("show")
          }, 100)

          setTimeout(() => {
            toast.classList.remove("show")
            setTimeout(() => {
              toast.remove()
            }, 300)
          }, 3000)
        })
        .finally(() => {
          this.classList.remove("rotating")
        })
    })
  }
}

// Declare formatCurrency function
function formatCurrency(value) {
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    minimumFractionDigits: 0,
  }).format(value)
}
