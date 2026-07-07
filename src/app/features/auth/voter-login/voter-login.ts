import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-voter-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './voter-login.html',
  styleUrls: ['./voter-login.css']
})
export class VoterLoginComponent implements OnInit {
  
  voterForm!: FormGroup;
  messages: string[] = [];
  isPasswordVisible = false;
  
  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    this.voterForm = this.fb.group({
      voterId: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  togglePassword(): void {
    this.isPasswordVisible = !this.isPasswordVisible;
  }

  onSubmit(): void {
    if (!this.voterForm.valid) {
      this.messages = ['Please enter your Voter ID and password.'];
      return;
    }

    const payload = {
      voter_id: this.voterForm.value.voterId,
      password: this.voterForm.value.password
    };

    this.api.voterLogin(payload).subscribe({
      next: () => {
        this.messages = [];
        this.router.navigate(['/voter-otp']);
      },
      error: error => {
        if (error?.status === 403 && error?.error?.requires_otp) {
          this.router.navigate(['/voter-otp']);
          return;
        }
        if (error?.status === 403 && error?.error?.requires_verification) {
          const voterId = error?.error?.voter_db_id;
          if (voterId) {
            this.router.navigate(['/verify-email', 'voter', voterId]);
            return;
          }
          this.messages = ['Account not verified. Please check your email for verification code.'];
          return;
        }
        const msg = error?.error?.error || 'Unable to login. Please try again.';
        this.messages = [msg];
      }
    });
  }

}