import frappe
from frappe.utils import today


def get_job_openings_tmplt(**args):

    city = args.get("city") or ""
    country = args.get("country") or "India"
    state = args.get("state") or ""
    postal_code = args.get("postal_code") or ""

    designation_description = args.get("job_description") or ""
    designation = (
        args.get("title")
        or args.get("designation")
        or ""
    )

    number_of_positions = args.get("number_of_positions") or 1
    target_date = args.get("target_date") or today()

    salary = args.get("salary") or 0
    work_experience = args.get("work_experience") or ""
    employment_type = args.get("job_type") or ""

    required_skills = args.get("required_skills") or ""
    requirements = args.get("requirements") or ""
    benefits = args.get("benefits") or ""

    current_date = today()

            
    job_description = f"""
        <span id="spandesc">
            <div class="ql-editor read-mode">
                {designation_description}
            </div>
        </span>
    """

    if requirements:
        job_description += f"""
            <br/>
            <span id="spanreq">
                <h3>Requirements</h3>
                <div class="ql-editor read-mode">
                    {requirements}
                </div>
                <div><br/></div>
            </span>
        """

    if benefits:
        job_description += f"""
            <br/>
            <span id="spanbenefits">
                <h3>Benefits</h3>
                <div class="ql-editor read-mode">
                    {benefits}
                </div>
                <div><br/></div>
            </span>
        """
        
    return frappe._dict({
        "data": [{
            "Posting_Title": designation,
            "Designation":designation,
            "Number_of_Positions": str(number_of_positions),
            "Job_Opening_Name": args.get("posting_title") or "",

            "Assigned_Recruiter": "578573000000579003",
            "Client_Name": args.get("department_name") or "",

            "Target_Date": str(target_date),
            "Job_Opening_Status": "In-progress",

            "Industry": args.get("industry") or "",
            "Salary": str(salary),
            "Currency": "INR",

            # "Department_Name": "578573000000590015",
            "Job_Department": args.get("job_department") or "",

            "Hiring_Manager": "578573000000579003",
            "Date_Opened": str(
                args.get("date_opened") or current_date
            ),

            "City": city,
            "Country": country,
            "Zip_Code": postal_code,
            "State": state,

            "Job_Type": employment_type,
            "Required_Skills": required_skills,
            "Work_Experience": str(work_experience),
            "Remote_Job": bool(args.get("remote_job")),

            "Job_Description": job_description,
            "Requirements": requirements,
            "Benefits": benefits,
        }]
    })

