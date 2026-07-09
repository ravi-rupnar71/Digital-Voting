import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-add-voter',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './add-voter.html',
  styleUrls: ['./add-voter.css']
})
export class AddVoterComponent implements OnInit {
  
  voterForm!: FormGroup;
  messages: string[] = [];

  constructor(private fb: FormBuilder, private api: ApiService, private router: Router) { }

  ngOnInit(): void {
    // Initialize the form with required fields
    this.voterForm = this.fb.group({
      voter_id: ['', Validators.required],
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', Validators.required]
    });
  }

  onSubmit(): void {
    if (this.voterForm.valid) {
      this.api.addVoter(this.voterForm.value).subscribe({
        next: data => {
          this.messages = ['Voter successfully added. Verification email sent.'];
          const voterEmail = this.voterForm.value.email;
          const verificationOtp = data?.verification_otp;
          const verificationEmailSent = data?.email_sent;
          this.voterForm.reset();
          const voterId = data?.voter_db_id;
          if (voterId) {
            this.router.navigate(['/verify-email', 'voter', voterId], {
              state: {
                verificationEmail: voterEmail,
                verificationOtp,
                emailSent: verificationEmailSent
              }
            });
          }
        },
        error: err => {
          const errorMessage = err?.error?.error || err?.message || 'Unable to add voter. Please try again.';
          this.messages = [errorMessage];
        }
      });
    } else {
      this.messages = ['Please fill out all required fields correctly.'];
    }
  }

}
