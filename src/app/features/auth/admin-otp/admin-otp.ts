import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-admin-otp',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './admin-otp.html',
  styleUrls: ['./admin-otp.css']
})
export class AdminOtpComponent implements OnInit, OnDestroy {
  
  otpForm!: FormGroup;
  messages: string[] = [];
  
  // Timer state
  secondsLeft: number = 300; // Example: 5 minutes
  private timerInterval: any;

  constructor(
    private fb: FormBuilder,
    private router: Router,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    // Initialize form with required validation and exactly 6 digits
    this.otpForm = this.fb.group({
      otp: ['', [Validators.required, Validators.pattern('^[0-9]{6}$')]]
    });

    this.startTimer();
  }

  ngOnDestroy(): void {
    // Prevent memory leaks by clearing the interval when the component is destroyed
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }

  startTimer(): void {
    this.timerInterval = setInterval(() => {
      if (this.secondsLeft > 0) {
        this.secondsLeft--;
      } else {
        clearInterval(this.timerInterval);
        this.messages = ['Your OTP has expired. Please request a new one.'];
        this.otpForm.get('otp')?.disable(); // Optionally disable input on expiry
      }
    }, 1000);
  }

  resendOtp(): void {
    this.api.adminOtp({ resend: true }).subscribe({
      next: () => {
        this.messages = ['A new code has been sent to your email.'];
        this.secondsLeft = 300; 
        this.otpForm.get('otp')?.enable();
        this.otpForm.reset();
        clearInterval(this.timerInterval);
        this.startTimer();
      },
      error: err => {
        const msg = err?.error?.error || 'Unable to resend OTP.';
        this.messages = [msg];
      }
    });
  }

  onSubmit(): void {
    if (this.otpForm.valid && this.secondsLeft > 0) {
      const otpValue = this.otpForm.value.otp;
      console.log('Verifying OTP:', otpValue);
      
      // TODO: Replace with your actual OTP verification service call
      this.api.adminOtp({ otp: otpValue }).subscribe({
        next: () => this.router.navigate(['/admin-dashboard']),
        error: err => {
          const msg = err?.error?.error || 'Invalid OTP. Please try again.';
          this.messages = [msg];
        }
      });
    }
  }

}