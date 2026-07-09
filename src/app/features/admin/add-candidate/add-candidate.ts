import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-add-candidate',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './add-candidate.html',
  styleUrls: ['./add-candidate.css']
})
export class AddCandidateComponent implements OnInit {
  
  candidateForm!: FormGroup;
  messages: string[] = [];

  constructor(private fb: FormBuilder, private api: ApiService, private router: Router) { }

  ngOnInit(): void {
    // Initialize the form and map the 'required' validations
    this.candidateForm = this.fb.group({
      name: ['', Validators.required],
      party: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  onSubmit(): void {
    if (this.candidateForm.valid) {
      this.api.addCandidate(this.candidateForm.value).subscribe({
        next: data => {
          this.messages = ['Candidate successfully added. Verification email sent.'];
          this.candidateForm.reset();
          const candidateId = data?.candidate_id;
          if (candidateId) {
            this.router.navigate(['/verify-email', 'candidate', candidateId], {
              state: {
                verificationEmail: this.candidateForm.value.email,
                verificationOtp: data?.verification_otp,
                emailSent: data?.email_sent,
                redirectTo: '/admin-dashboard'
              }
            });
          }
        },
        error: err => {
          const errorMessage = err?.error?.error || err?.message || 'Unable to add candidate. Please try again.';
          this.messages = [errorMessage];
        }
      });
    } else {
      this.messages = ['Please fill out all required fields correctly.'];
    }
  }

}