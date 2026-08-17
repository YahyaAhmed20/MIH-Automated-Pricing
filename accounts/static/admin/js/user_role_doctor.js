(function () {

    function updateDoctorFields() {

        const roleField =
            document.getElementById("id_role");

        const doctorField =
            document.getElementById("id_doctor_name");

        if (!roleField) {
            return;
        }

        const doctorRow = doctorField
            ? doctorField.closest(".form-row")
            : null;

        const allowedDoctorsContainer =
            document.getElementById("id_allowed_doctors");

        const allowedDoctorsRow =
            allowedDoctorsContainer
                ? allowedDoctorsContainer.closest(".form-row")
                : null;

        const selectedOption =
            roleField.options[roleField.selectedIndex];

        const roleName = selectedOption
            ? selectedOption.text.trim()
            : "";

        const isDoctor = roleName === "Doctor";


        // =========================================
        // الطبيب الأساسي
        // =========================================

        if (doctorRow) {
            doctorRow.style.display =
                isDoctor ? "" : "none";
        }


        // =========================================
        // الأطباء الإضافيين
        // =========================================

        if (allowedDoctorsRow) {
            allowedDoctorsRow.style.display =
                isDoctor ? "" : "none";
        }


        // =========================================
        // لو مش Doctor
        // =========================================

        if (!isDoctor) {

            if (doctorField) {
                doctorField.value = "";
            }

            if (allowedDoctorsContainer) {

                const checkboxes =
                    allowedDoctorsContainer.querySelectorAll(
                        'input[type="checkbox"]'
                    );

                checkboxes.forEach(function (checkbox) {

                    checkbox.checked = false;
                    checkbox.disabled = false;

                });
            }

            return;
        }


        // =========================================
        // استبعاد الطبيب الأساسي
        // =========================================

        if (
            doctorField &&
            allowedDoctorsContainer
        ) {

            const selectedDoctor =
                doctorField.value;

            const checkboxes =
                allowedDoctorsContainer.querySelectorAll(
                    'input[type="checkbox"]'
                );

            checkboxes.forEach(function (checkbox) {

                const wrapper =
                    checkbox.closest("label") ||
                    checkbox.closest("li") ||
                    checkbox.parentElement;

                if (checkbox.value === selectedDoctor) {

                    checkbox.checked = false;
                    checkbox.disabled = true;

                    if (wrapper) {
                        wrapper.style.display = "none";
                    }

                } else {

                    checkbox.disabled = false;

                    if (wrapper) {
                        wrapper.style.display = "";
                    }

                }

            });
        }
    }


    function initDoctorFields() {

        const roleField =
            document.getElementById("id_role");

        const doctorField =
            document.getElementById("id_doctor_name");

        if (!roleField) {
            return;
        }


        roleField.addEventListener(
            "change",
            updateDoctorFields
        );


        if (doctorField) {

            doctorField.addEventListener(
                "change",
                updateDoctorFields
            );

        }


        updateDoctorFields();
    }


    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initDoctorFields
        );

    } else {

        initDoctorFields();

    }

})();