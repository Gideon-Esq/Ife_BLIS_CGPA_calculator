document.addEventListener('DOMContentLoaded', () => {
    const partSelect = document.getElementById('part-select');
    const semesterSelect = document.getElementById('semester-select');
    const courseInputArea = document.getElementById('course-input-area');
    const semesterGpaDisplay = document.getElementById('semester-gpa-display');
    const cumulativeGpaDisplay = document.getElementById('cumulative-gpa-display');
    const addSemesterBtn = document.getElementById('add-semester-btn');
    const resetSessionBtn = document.getElementById('reset-session-btn');
    const saveCalculationBtn = document.getElementById('save-calculation-btn');
    const notificationArea = document.getElementById('notification-area');
    const sessionSummaryList = document.querySelector('#session-summary ul');

    const showNotification = (message, type = 'success') => {
        notificationArea.textContent = message;
        notificationArea.className = `notification ${type} show`;
        setTimeout(() => {
            notificationArea.classList.remove('show');
        }, 3000);
    };

    const setLoadingState = (isLoading) => {
        addSemesterBtn.disabled = isLoading;
        resetSessionBtn.disabled = isLoading;
        saveCalculationBtn.disabled = isLoading;
        if (isLoading) {
            addSemesterBtn.innerHTML = '<i class="material-icons">hourglass_top</i> Adding...';
        } else {
            addSemesterBtn.innerHTML = '<i class="material-icons">add_circle_outline</i> Add Semester';
        }
    };

    const updateButtonStates = () => {
        const hasGrades = courseInputArea.querySelector('select[name="grade"]');
        const sessionHasData = sessionSummaryList.children.length > 0;
        addSemesterBtn.disabled = !hasGrades;
        saveCalculationBtn.disabled = !sessionHasData;
    };

    async function fetchCourses() {
        const part = partSelect.value;
        const semester = semesterSelect.value;
        courseInputArea.innerHTML = '';
        updateButtonStates();

        if (part && semester) {
            setLoadingState(true);
            try {
                const response = await fetch(`/api/courses/${part}/${semester}`);
                if (!response.ok) throw new Error('Failed to load courses.');
                const courses = await response.json();
                renderCourses(courses);
            } catch (error) {
                showNotification(error.message, 'error');
            } finally {
                setLoadingState(false);
                updateButtonStates();
            }
        }
    }

    function renderCourses(courses) {
        if (courses.length === 0) {
            courseInputArea.innerHTML = '<p>No courses found for this selection.</p>';
            return;
        }
        const table = document.createElement('table');
        table.innerHTML = `
            <thead>
                <tr><th>Course Code</th><th>Course Title</th><th>Course Unit</th><th>Grade</th></tr>
            </thead>
            <tbody>
                ${courses.map(course => `
                    <tr>
                        <td>${course.course_code}</td>
                        <td>
                            ${course.course_title}
                            ${course.is_carry_over ? '<span class="carry-over-tag">(Carry-over)</span>' : ''}
                        </td>
                        <td>${course.course_unit}</td>
                        <td>
                            <select name="grade" data-course-code="${course.course_code}">
                                <option value="" ${!course.grade ? 'selected' : ''}>--</option>
                                <option value="A" ${course.grade === 'A' ? 'selected' : ''}>A</option>
                                <option value="B" ${course.grade === 'B' ? 'selected' : ''}>B</option>
                                <option value="C" ${course.grade === 'C' ? 'selected' : ''}>C</option>
                                <option value="D" ${course.grade === 'D' ? 'selected' : ''}>D</option>
                                <option value="E" ${course.grade === 'E' ? 'selected' : ''}>E</option>
                                <option value="F" ${course.grade === 'F' ? 'selected' : ''}>F</option>
                            </select>
                        </td>
                    </tr>
                `).join('')}
            </tbody>`;
        courseInputArea.appendChild(table);
    }

    async function addSemesterToCalculation() {
        const part = partSelect.value;
        const semester = semesterSelect.value;
        if (!part || !semester) {
            showNotification('Please select a Part and Semester.', 'error');
            return;
        }

        const grades = Array.from(courseInputArea.querySelectorAll('select[name="grade"]'))
            .filter(select => select.value)
            .map(select => ({
                course_code: select.dataset.courseCode,
                grade: select.value
            }));

        if (grades.length === 0) {
            showNotification('Please enter at least one grade.', 'error');
            return;
        }

        setLoadingState(true);
        try {
            const response = await fetch('/api/add_semester', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ part, semester, grades }),
            });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to add semester');
            }
            const result = await response.json();
            updateDisplays(result);
            showNotification('Semester added successfully!', 'success');
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            setLoadingState(false);
            updateButtonStates();
        }
    }

    async function resetSession() {
        setLoadingState(true);
        try {
            await fetch('/api/reset_session', { method: 'POST' });
            semesterGpaDisplay.textContent = '0.00';
            cumulativeGpaDisplay.textContent = '0.00';
            sessionSummaryList.innerHTML = '';
            courseInputArea.innerHTML = '';
            partSelect.value = '';
            semesterSelect.value = '';
            showNotification('New calculation started.', 'success');
        } catch (error) {
            showNotification('Failed to reset session.', 'error');
        } finally {
            setLoadingState(false);
            updateButtonStates();
        }
    }

    function updateDisplays(result) {
        semesterGpaDisplay.textContent = result.semester_gpa.toFixed(2);
        cumulativeGpaDisplay.textContent = result.cumulative_gpa.toFixed(2);
        sessionSummaryList.innerHTML = result.session_summary.map(item =>
            `<li>Part ${item.part} ${item.semester} - GPA: ${item.gpa.toFixed(2)}</li>`
        ).join('');
    }

    async function saveCalculation() {
        if (sessionSummaryList.children.length === 0) {
            showNotification('No data to save. Please add at least one semester.', 'error');
            return;
        }
        setLoadingState(true);
        try {
            const response = await fetch('/api/save_calculation', { method: 'POST' });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || 'Failed to save calculation');
            }
            const result = await response.json();
            showNotification(`Calculation saved with ID: ${result.record_id}`, 'success');
            await resetSession();
        } catch (error) {
            showNotification(error.message, 'error');
        } finally {
            setLoadingState(false);
        }
    }

    partSelect.addEventListener('change', fetchCourses);
    semesterSelect.addEventListener('change', fetchCourses);
    addSemesterBtn.addEventListener('click', addSemesterToCalculation);
    resetSessionBtn.addEventListener('click', resetSession);
    saveCalculationBtn.addEventListener('click', saveCalculation);

    // Initial button states and data load
    function initializePage() {
        // This data is now passed from the backend template
        const initialCGPA = parseFloat(cumulativeGpaDisplay.dataset.initialCgpa || 0);
        const initialSummary = JSON.parse(sessionSummaryList.dataset.initialSummary || '[]');

        cumulativeGpaDisplay.textContent = initialCGPA.toFixed(2);

        if (initialSummary.length > 0) {
            sessionSummaryList.innerHTML = initialSummary.map(item =>
                `<li>Part ${item.part} ${item.semester} - GPA: ${item.gpa.toFixed(2)}</li>`
            ).join('');
        }

        updateButtonStates();
    }

    partSelect.addEventListener('change', fetchCourses);
    semesterSelect.addEventListener('change', fetchCourses);
    addSemesterBtn.addEventListener('click', addSemesterToCalculation);
    resetSessionBtn.addEventListener('click', resetSession);
    saveCalculationBtn.addEventListener('click', saveCalculation);

    initializePage();
});
