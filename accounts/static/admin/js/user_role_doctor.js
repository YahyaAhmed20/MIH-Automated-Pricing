(function () {
    function updateDoctorField() {
        const roleField = document.getElementById("id_role");
        const doctorField = document.getElementById("id_doctor_name");

        if (!roleField || !doctorField) {
            return;
        }

        const doctorRow = doctorField.closest(".form-row");

        if (!doctorRow) {
            return;
        }

        const selectedOption =
            roleField.options[roleField.selectedIndex];

        const roleName = selectedOption
            ? selectedOption.text.trim()
            : "";

        if (roleName === "Doctor") {
            doctorRow.style.display = "";
        } else {
            doctorRow.style.display = "none";
            doctorField.value = "";
        }
    }

    function initDoctorField() {
        const roleField = document.getElementById("id_role");

        if (!roleField) {
            return;
        }

        roleField.addEventListener(
            "change",
            updateDoctorField
        );

        updateDoctorField();
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initDoctorField
        );
    } else {
        initDoctorField();
    }
})();