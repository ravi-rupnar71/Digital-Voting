import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-edit-candidate',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './edit-candidate.html',
  styleUrls: ['./edit-candidate.css']
})
export class EditCandidateComponent implements OnInit {
  
  editForm!: FormGroup;
  messages: string[] = [];
  candidateId!: number;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit(): void {
    // 1. Initialize the form (password is optional)
    this.editForm = this.fb.group({
      name: ['', Validators.required],
      party: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: [''] 
    });

    // 2. Get the candidate ID from the URL (e.g., /edit-candidate/:id)
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.candidateId = +id;
        this.loadCandidateData(this.candidateId);
      }
    });
  }

  loadCandidateData(id: number): void {
    // TODO: Call your CandidateService to fetch data from your API
    // Example Mock Data:
    const mockDataFromApi = {
      name: 'Candidate A',
      party: 'Party One',
      email: 'candidate@example.com'
    };

    // Pre-fill the form with the fetched data
    this.editForm.patchValue({
      name: mockDataFromApi.name,
      party: mockDataFromApi.party,
      email: mockDataFromApi.email
    });
  }

  onSubmit(): void {
    if (this.editForm.valid) {
      // TODO: Call your CandidateService to send the PUT/POST request
      const updatedData = this.editForm.value;
      console.log('Submitting updated candidate data:', updatedData);
      
      // Mock success behavior
      this.messages = ['Candidate details updated successfully.'];
      
      // Optional: automatically route back to dashboard after a delay
      // setTimeout(() => this.router.navigate(['/admin-dashboard']), 2000);
    } else {
      this.messages = ['Please ensure all required fields are filled out correctly.'];
    }
  }

}