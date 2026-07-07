document.addEventListener("DOMContentLoaded", () => {
  const addFamilyMemberBtn = document.getElementById("addFamilyMember")
  const familyMembersContainer = document.getElementById("familyMembersContainer")
  let familyMemberCount = 0

  // Handle marital status change
  const maritalStatusSelect = document.getElementById("marital_status")
  const spouseSection = document.getElementById("spouseSection")
  const childrenSection = document.getElementById("childrenSection")

  if (maritalStatusSelect) {
    maritalStatusSelect.addEventListener("change", () => {
      const status = maritalStatusSelect.value
      
      // Show/hide sections based on marital status
      if (status === "Married") {
        spouseSection.style.display = "block"
        childrenSection.style.display = "block"
      } else if (status === "Divorced") {
        spouseSection.style.display = "none"
        childrenSection.style.display = "block"
      } else {
        spouseSection.style.display = "none"
        childrenSection.style.display = "none"
      }

      // Clear spouse fields if hidden
      if (spouseSection.style.display === "none") {
        const spouseFields = spouseSection.querySelectorAll("input, select")
        spouseFields.forEach(field => field.value = "")
      }

      // Clear children fields if hidden
      if (childrenSection.style.display === "none") {
        const childrenFields = childrenSection.querySelectorAll("input, select")
        childrenFields.forEach(field => field.value = "")
        // Clear all children
        familyMembersContainer.innerHTML = ""
        familyMemberCount = 0
      }
    })
  }

  if (addFamilyMemberBtn) {
    addFamilyMemberBtn.addEventListener("click", addFamilyMember)
  }

  function addFamilyMember() {
    if (familyMemberCount >= 2) {
      alert("You can add a maximum of 2 children.")
      return
    }

    familyMemberCount++

    const familyMemberDiv = document.createElement("div")
    familyMemberDiv.className = "family-member"
    familyMemberDiv.innerHTML = `
            <div class="family-member-header">
                <h4 class="family-member-title">Child ${familyMemberCount}</h4>
                <button type="button" class="remove-family-member" onclick="removeFamilyMember(this)">
                    Remove
                </button>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="family_name_${familyMemberCount}">Full Name *</label>
                    <input type="text" id="family_name_${familyMemberCount}" name="family_name[]" required>
                </div>
                
                <div class="form-group">
                    <label for="family_relationship_${familyMemberCount}">Gender *</label>
                    <select id="family_relationship_${familyMemberCount}" name="family_relationship[]" required>
                        <option value="">Select Gender</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                    </select>
                </div>
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="family_dob_${familyMemberCount}">Date of Birth *</label>
                    <input type="date" id="family_dob_${familyMemberCount}" name="family_dob[]" required>
                </div>
                
                <div class="form-group">
                    <label for="family_phone_${familyMemberCount}">Phone Number</label>
                    <input type="tel" id="family_phone_${familyMemberCount}" name="family_phone[]">
                </div>
            </div>
        `

    familyMembersContainer.appendChild(familyMemberDiv)

    // Scroll to the new family member
    familyMemberDiv.scrollIntoView({ behavior: "smooth", block: "center" })
  }

  // Make removeFamilyMember globally accessible
  window.removeFamilyMember = (button) => {
    const familyMemberDiv = button.closest(".family-member")
    familyMemberDiv.remove()
    familyMemberCount--
    updateFamilyMemberNumbers()
  }

  function updateFamilyMemberNumbers() {
    const familyMembers = document.querySelectorAll(".family-member")
    familyMembers.forEach((member, index) => {
      const title = member.querySelector(".family-member-title")
      title.textContent = `Child ${index + 1}`
    })
    familyMemberCount = familyMembers.length
  }

  // Form validation
  const employeeForm = document.getElementById("employeeForm")
  if (employeeForm) {
    employeeForm.addEventListener("submit", (e) => {
      const requiredFields = employeeForm.querySelectorAll("[required]")
      let isValid = true

      requiredFields.forEach((field) => {
        if (!field.value.trim()) {
          field.style.borderColor = "#e74c3c"
          isValid = false
        } else {
          field.style.borderColor = "#ddd"
        }
      })

      if (!isValid) {
        e.preventDefault()
        alert("Please fill in all required fields.")
      }
    })
  }

  // Auto-hide flash messages
  const flashMessages = document.querySelectorAll(".flash-message")
  flashMessages.forEach((message) => {
    setTimeout(() => {
      message.style.opacity = "0"
      setTimeout(() => {
        message.remove()
      }, 300)
    }, 5000)
  })
})
