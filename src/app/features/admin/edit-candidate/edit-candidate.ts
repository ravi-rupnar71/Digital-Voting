import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';

import { ApiService } from '../../../core/services/api';

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
  originalEmail = '';

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private apiService: ApiService
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
    this.apiService.getCandidate(id).subscribe({
      next: (candidateData) => {
        this.originalEmail = candidateData.email || '';
        this.editForm.patchValue({
          name: candidateData.name,
          party: candidateData.party,
          email: candidateData.email
        });
      },
      error: () => {
        this.messages = ['Unable to load candidate details.'];
      }
    });
  }

  onSubmit(): void {
    if (this.editForm.valid) {
      const updatedData = this.editForm.value;
      this.apiService.updateCandidate(this.candidateId, updatedData).subscribe({
        next: () => {
          this.messages = ['Please verify the updated details to complete the save.'];
          this.router.navigate(['/verify-email', 'candidate', this.candidateId], {
            state: { verificationEmail: updatedData.email, redirectTo: '/admin-dashboard' }
          });
        },
        error: () => {
          this.messages = ['Unable to update candidate details. Please try again.'];
        }
      });
    } else {
      this.messages = ['Please ensure all required fields are filled out correctly.'];
    }
  }

}