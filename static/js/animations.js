document.addEventListener("DOMContentLoaded", () => {
  // Initialize macOS-style animations
  initMacOSAnimations()

  // Initialize parallax effects
  initParallaxEffects()

  // Initialize scroll animations
  initScrollAnimations()

  // Initialize hover effects
  initHoverEffects()
})

// macOS-style animations
function initMacOSAnimations() {
  // Smooth page transitions
  document.querySelectorAll('a:not([target="_blank"]):not([href^="#"]):not([href^="javascript:"])').forEach((link) => {
    link.addEventListener("click", function (e) {
      const href = this.getAttribute("href")

      if (href && href.startsWith("/") && !this.hasAttribute("data-no-transition")) {
        e.preventDefault()

        document.body.classList.add("page-transition")

        setTimeout(() => {
          window.location.href = href
        }, 300)
      }
    })
  })

  // Add transition class to body when page loads
  if (!document.body.classList.contains("page-loaded")) {
    document.body.classList.add("page-loaded")
  }

  // Button press effect
  document.querySelectorAll(".btn").forEach((button) => {
    button.addEventListener("mousedown", function () {
      this.classList.add("btn-pressed")
    })

    button.addEventListener("mouseup", function () {
      this.classList.remove("btn-pressed")
    })

    button.addEventListener("mouseleave", function () {
      this.classList.remove("btn-pressed")
    })
  })

  // Card hover effect with subtle rotation
  document.querySelectorAll(".card").forEach((card) => {
    card.addEventListener("mousemove", function (e) {
      const rect = this.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const rotateX = (y - centerY) / 20
      const rotateY = (centerX - x) / 20

      this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(10px)`
    })

    card.addEventListener("mouseleave", function () {
      this.style.transform = "perspective(1000px) rotateX(0) rotateY(0) translateZ(0)"
    })
  })
}

// Parallax effects
function initParallaxEffects() {
  // Header parallax
  const header = document.querySelector(".app-header")

  if (header) {
    window.addEventListener("scroll", () => {
      const scrollPosition = window.scrollY

      if (scrollPosition > 0) {
        header.classList.add("scrolled")
        header.style.backdropFilter = `blur(${Math.min(8, scrollPosition / 10)}px)`
      } else {
        header.classList.remove("scrolled")
        header.style.backdropFilter = "blur(0px)"
      }
    })
  }

  // Background parallax
  const parallaxElements = document.querySelectorAll("[data-parallax]")

  parallaxElements.forEach((element) => {
    const speed = Number.parseFloat(element.getAttribute("data-parallax-speed") || "0.5")

    window.addEventListener("scroll", () => {
      const scrollPosition = window.scrollY
      const offset = scrollPosition * speed

      element.style.transform = `translateY(${offset}px)`
    })
  })
}

// Scroll animations
function initScrollAnimations() {
  const animatedElements = document.querySelectorAll("[data-animate]")

  if (animatedElements.length > 0) {
    // Create intersection observer
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const element = entry.target
            const animation = element.getAttribute("data-animate")
            const delay = element.getAttribute("data-animate-delay") || "0"

            setTimeout(() => {
              element.classList.add("animated", animation)
            }, Number.parseInt(delay))

            observer.unobserve(element)
          }
        })
      },
      {
        threshold: 0.1,
      },
    )

    // Observe elements
    animatedElements.forEach((element) => {
      observer.observe(element)
    })
  }
}

// Hover effects
function initHoverEffects() {
  // Glow effect
  document.querySelectorAll("[data-glow]").forEach((element) => {
    element.addEventListener("mousemove", function (e) {
      const rect = this.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      this.style.setProperty("--glow-x", `${x}px`)
      this.style.setProperty("--glow-y", `${y}px`)
    })
  })

  // Magnetic effect
  document.querySelectorAll("[data-magnetic]").forEach((element) => {
    element.addEventListener("mousemove", function (e) {
      const rect = this.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const deltaX = (x - centerX) / 8
      const deltaY = (y - centerY) / 8

      this.style.transform = `translate(${deltaX}px, ${deltaY}px)`
    })

    element.addEventListener("mouseleave", function () {
      this.style.transform = "translate(0, 0)"
    })
  })
}

// Add page transition listener
window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    document.body.classList.remove("page-transition")
  }
})

// Add smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach((anchor) => {
  anchor.addEventListener("click", function (e) {
    e.preventDefault()

    const targetId = this.getAttribute("href")
    const targetElement = document.querySelector(targetId)

    if (targetElement) {
      window.scrollTo({
        top: targetElement.offsetTop - 80, // Adjust for header height
        behavior: "smooth",
      })
    }
  })
})
