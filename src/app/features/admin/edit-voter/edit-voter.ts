import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

@Component({
  selector: 'app-edit-voter',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './edit-voter.html',
  styleUrls: ['./edit-voter.css']
})
export class EditVoterComponent implements OnInit {
  
  editVoterForm!: FormGroup;
  messages: string[] = [];
  voterDbId!: number; // The database ID of the voter, extracted from the route

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router
  ) { }

  ngOnInit(): void {
    // 1. Initialize the form (password is optional, so no required validator)
    this.editVoterForm = this.fb.group({
      voter_id: ['', Validators.required],
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: [''] 
    });

    // 2. Extract the voter ID from the URL (e.g., /edit-voter/:id)
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.voterDbId = +id;
        this.loadVoterData(this.voterDbId);
      }
    });
  }

  loadVoterData(id: number): void {
    // TODO: Call your VoterService to fetch data from your backend
    // Example Mock Data representing what you'd get from the server:
    const mockDataFromApi = {
      voter_id: 'V003',
      name: 'Jaysinh Shinde',
      email: 'voter@example.com'
    };

    // 3. Pre-fill the form with the fetched data
    this.editVoterForm.patchValue({
      voter_id: mockDataFromApi.voter_id,
      name: mockDataFromApi.name,
      email: mockDataFromApi.email
    });
  }

  onSubmit(): void {
    if (this.editVoterForm.valid) {
      // TODO: Call your VoterService to send the PUT/POST request
      const updatedData = this.editVoterForm.value;
      console.log('Submitting updated voter data:', updatedData);
      
      // Mock success behavior
      this.messages = ['Voter details updated successfully.'];
      
      // Optional: automatically route back to dashboard after a delay
      // setTimeout(() => this.router.navigate(['/admin-dashboard']), 2000);
    } else {
      this.messages = ['Please ensure all required fields are filled out correctly.'];
    }
  }

}