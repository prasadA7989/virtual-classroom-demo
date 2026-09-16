import React, { useEffect, useState } from "react";

function App() {

    const [students, setStudents] = useState([]);

    const [form, setForm] = useState({
        name: "",
        date_of_entry: "",
        course: "",
        payment_status: "Pending",
        subscription_end: ""
    });

    const [document, setDocument] = useState(null);

    const loadStudents = async () => {

        const response = await fetch("/api/students");

        const data = await response.json();

        setStudents(data);
    };

    useEffect(() => {
        loadStudents();
    }, []);

    const handleChange = (event) => {

        setForm({
            ...form,
            [event.target.name]: event.target.value
        });
    };

    const submitStudent = async (event) => {

        event.preventDefault();

        const data = new FormData();

        Object.entries(form).forEach(([key, value]) => {
            data.append(key, value);
        });

        if (document) {
            data.append("document", document);
        }

        const response = await fetch("/api/students", {
            method: "POST",
            body: data
        });

        if (response.ok) {

            setForm({
                name: "",
                date_of_entry: "",
                course: "",
                payment_status: "Pending",
                subscription_end: ""
            });

            setDocument(null);

            loadStudents();
        }
    };

    const deleteStudent = async (id) => {

        await fetch(`/api/students/${id}`, {
            method: "DELETE"
        });

        loadStudents();
    };

    const openDocument = async (id) => {

        const response = await fetch(
            `/api/students/${id}/document`
        );

        if (!response.ok) {
            alert("No document available");
            return;
        }

        const data = await response.json();

        window.open(data.url, "_blank");
    };

    return (

        <div className="container">

            <h1>Virtual Classroom Platform V2</h1>

            <h2>Student Registration</h2>

            <form onSubmit={submitStudent}>

                <input
                    name="name"
                    placeholder="Student Name"
                    value={form.name}
                    onChange={handleChange}
                    required
                />

                <input
                    type="date"
                    name="date_of_entry"
                    value={form.date_of_entry}
                    onChange={handleChange}
                    required
                />

                <input
                    name="course"
                    placeholder="Course"
                    value={form.course}
                    onChange={handleChange}
                    required
                />

                <select
                    name="payment_status"
                    value={form.payment_status}
                    onChange={handleChange}
                >

                    <option>Paid</option>

                    <option>Pending</option>

                    <option>
                        Clarification Required
                    </option>

                </select>

                <input
                    type="date"
                    name="subscription_end"
                    value={form.subscription_end}
                    onChange={handleChange}
                    required
                />

                <input
                    type="file"
                    onChange={
                        (event) =>
                            setDocument(
                                event.target.files[0]
                            )
                    }
                />

                <button type="submit">
                    Add Student
                </button>

            </form>

            <h2>Students</h2>

            <table>

                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Entry Date</th>
                        <th>Course</th>
                        <th>Payment</th>
                        <th>Subscription End</th>
                        <th>Document</th>
                        <th>Action</th>
                    </tr>
                </thead>

                <tbody>

                {students.map((student) => (

                    <tr key={student.id}>

                        <td>{student.id}</td>

                        <td>{student.name}</td>

                        <td>
                            {student.date_of_entry}
                        </td>

                        <td>{student.course}</td>

                        <td>
                            {student.payment_status}
                        </td>

                        <td>
                            {student.subscription_end}
                        </td>

                        <td>

                            {student.document_key ? (

                                <button
                                    onClick={() =>
                                        openDocument(
                                            student.id
                                        )
                                    }
                                >
                                    View
                                </button>

                            ) : "No File"}

                        </td>

                        <td>

                            <button
                                onClick={() =>
                                    deleteStudent(
                                        student.id
                                    )
                                }
                            >
                                Delete
                            </button>

                        </td>

                    </tr>

                ))}

                </tbody>

            </table>

        </div>
    );
}

export default App;
