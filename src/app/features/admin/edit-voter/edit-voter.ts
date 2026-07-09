import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { ApiService } from '../../../core/services/api';

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
  originalEmail = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
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
    this.apiService.getVoter(id).subscribe({
      next: (voterData) => {
        this.originalEmail = voterData.email || '';
        this.editVoterForm.patchValue({
          voter_id: voterData.voter_id,
          name: voterData.name,
          email: voterData.email
        });
      },
      error: () => {
        this.messages = ['Unable to load voter details.'];
      }
    });
  }

  onSubmit(): void {
    if (this.editVoterForm.valid) {
      const updatedData = this.editVoterForm.value;
      this.apiService.updateVoter(this.voterDbId, updatedData).subscribe({
        next: () => {
          this.messages = ['Please verify the updated details to complete the save.'];
          this.router.navigate(['/verify-email', 'voter', this.voterDbId], {
            state: { verificationEmail: updatedData.email, redirectTo: '/admin-dashboard' }
          });
        },
        error: () => {
          this.messages = ['Unable to update voter details. Please try again.'];
        }
      });
    } else {
      this.messages = ['Please ensure all required fields are filled out correctly.'];
    }
  }

}