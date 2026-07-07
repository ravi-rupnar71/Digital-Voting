import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-voter-otp',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './voter-otp.html',
  styleUrls: ['./voter-otp.css']
})
export class VoterOtpComponent implements OnInit {
  
  otpForm!: FormGroup;
  messages: string[] = [];

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    this.otpForm = this.fb.group({
      otp: ['', [Validators.required, Validators.pattern('^[0-9]{6}$')]]
    });
  }

  resendOtp(): void {
    this.api.voterOtp({ resend: true }).subscribe({
      next: () => {
        this.messages = ['A new verification code has been sent to your email.'];
        this.otpForm.reset();
      },
      error: error => {
        const msg = error?.error?.error || 'Unable to resend code. Please try again.';
        this.messages = [msg];
      }
    });
  }

  onSubmit(): void {
    if (!this.otpForm.valid) {
      this.messages = ['Please enter the 6-digit code.'];
      return;
    }

    const payload = {
      otp: this.otpForm.value.otp
    };

    this.api.voterOtp(payload).subscribe({
      next: () => {
        this.messages = [];
        this.router.navigate(['/vote']);
      },
      error: error => {
        const msg = error?.error?.error || 'Invalid OTP. Please try again.';
        this.messages = [msg];
      }
    });
  }

}