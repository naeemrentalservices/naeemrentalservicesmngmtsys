document.addEventListener("DOMContentLoaded", () => {
  // Initialize user menu dropdown
  initUserMenu()

  // Initialize mobile navigation
  initMobileNav()

  // Initialize modals
  initModals()

  // Initialize tooltips
  initTooltips()

  // Initialize alerts auto-dismiss
  initAlertsDismiss()

  // Add macOS-style animations
  initMacOSAnimations()
})

// User menu dropdown
function initUserMenu() {
  const userMenuTrigger = document.querySelector(".user-menu-trigger")
  const userMenu = document.querySelector(".user-menu")

  if (userMenuTrigger && userMenu) {
    userMenuTrigger.addEventListener("click", (e) => {
      e.stopPropagation()
      userMenu.classList.toggle("open")
    })

    // Close when clicking outside
    document.addEventListener("click", () => {
      userMenu.classList.remove("open")
    })
  }
}

// Mobile navigation
function initMobileNav() {
  const mobileMenuToggle = document.querySelector(".mobile-menu-toggle")
  const mobileMenu = document.querySelector(".mobile-menu")

  if (mobileMenuToggle && mobileMenu) {
    mobileMenuToggle.addEventListener("click", () => {
      mobileMenu.classList.toggle("open")
      document.body.classList.toggle("menu-open")
    })
  }
}

// Modal functionality
function initModals() {
  // Open modals
  document.querySelectorAll('[data-toggle="modal"]').forEach((trigger) => {
    trigger.addEventListener("click", function () {
      const targetId = this.getAttribute("data-target")
      const modal = document.querySelector(targetId)

      if (modal) {
        modal.classList.add("show")
        document.body.style.overflow = "hidden"
      }
    })
  })

  // Close modals
  document.querySelectorAll('.modal-close, [data-dismiss="modal"]').forEach((closeBtn) => {
    closeBtn.addEventListener("click", function () {
      const modal = this.closest(".modal-backdrop")

      if (modal) {
        modal.classList.remove("show")
        document.body.style.overflow = ""
      }
    })
  })

  // Close modal when clicking on backdrop
  document.querySelectorAll(".modal-backdrop").forEach((backdrop) => {
    backdrop.addEventListener("click", function (e) {
      if (e.target === this) {
        this.classList.remove("show")
        document.body.style.overflow = ""
      }
    })
  })
}

// Tooltips
function initTooltips() {
  document.querySelectorAll("[data-tooltip]").forEach((element) => {
    element.addEventListener("mouseenter", function () {
      const tooltipText = this.getAttribute("data-tooltip")

      const tooltip = document.createElement("div")
      tooltip.className = "tooltip"
      tooltip.textContent = tooltipText

      document.body.appendChild(tooltip)

      const rect = this.getBoundingClientRect()
      const tooltipRect = tooltip.getBoundingClientRect()

      tooltip.style.top = `${rect.top - tooltipRect.height - 10}px`
      tooltip.style.left = `${rect.left + (rect.width / 2) - tooltipRect.width / 2}px`
      tooltip.style.opacity = "1"

      this.addEventListener(
        "mouseleave",
        () => {
          tooltip.remove()
        },
        { once: true },
      )
    })
  })
}

// Auto-dismiss alerts
function initAlertsDismiss() {
  document.querySelectorAll(".alert").forEach((alert) => {
    if (!alert.classList.contains("alert-persistent")) {
      setTimeout(() => {
        alert.style.opacity = "0"
        setTimeout(() => {
          alert.remove()
        }, 300)
      }, 5000)
    }
  })

  // Close button for alerts
  document.querySelectorAll(".alert .close").forEach((closeBtn) => {
    closeBtn.addEventListener("click", function () {
      const alert = this.closest(".alert")

      alert.style.opacity = "0"
      setTimeout(() => {
        alert.remove()
      }, 300)
    })
  })
}

// macOS-style animations
function initMacOSAnimations() {
  // Card hover effect
  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-5px)"
      this.style.boxShadow = "var(--shadow-lg)"
    })

    card.addEventListener("mouseleave", function () {
      this.style.transform = ""
      this.style.boxShadow = ""
    })
  })

  // Button hover effect
  document.querySelectorAll(".btn").forEach((btn) => {
    btn.addEventListener("mouseenter", function () {
      this.style.transform = "scale(1.05)"
    })

    btn.addEventListener("mouseleave", function () {
      this.style.transform = ""
    })

    btn.addEventListener("mousedown", function () {
      this.style.transform = "scale(0.95)"
    })

    btn.addEventListener("mouseup", function () {
      this.style.transform = "scale(1.05)"
    })
  })
}

// Confirm delete
function confirmDelete(message, formId) {
  if (confirm(message)) {
    document.getElementById(formId).submit()
  }
  return false
}

// Format currency
function formatCurrency(amount) {
  return new Intl.NumberFormat("en-PK", {
    style: "currency",
    currency: "PKR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date)
}

// Image preview for file inputs
function previewImage(input, previewId) {
  const preview = document.getElementById(previewId)
  const file = input.files[0]

  if (file) {
    const reader = new FileReader()

    reader.onload = (e) => {
      preview.src = e.target.result
      preview.style.display = "block"
    }

    reader.readAsDataURL(file)
  }
}

// Toggle password visibility
function togglePasswordVisibility(inputId, iconId) {
  const input = document.getElementById(inputId)
  const icon = document.getElementById(iconId)

  if (input.type === "password") {
    input.type = "text"
    icon.classList.remove("fa-eye")
    icon.classList.add("fa-eye-slash")
  } else {
    input.type = "password"
    icon.classList.remove("fa-eye-slash")
    icon.classList.add("fa-eye")
  }
}
