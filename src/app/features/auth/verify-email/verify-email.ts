import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ApiService } from '../../../core/services/api';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterModule],
  templateUrl: './verify-email.html',
  styleUrls: ['./verify-email.css']
})
export class VerifyEmailComponent implements OnInit, OnDestroy {
  
  verifyForm!: FormGroup;
  messages: string[] = [];

  // Dynamic variables extracted from the route
  targetId!: number;
  kind: 'voter' | 'candidate' = 'voter'; // defaults to voter
  targetEmail: string = '';

  // Timer state
  secondsLeft: number = 300; 
  private timerInterval: any;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private router: Router,
    private api: ApiService
  ) { }

  ngOnInit(): void {
    // 1. Initialize form
    this.verifyForm = this.fb.group({
      otp: ['', [Validators.required, Validators.pattern('^[0-9]{6}$')]]
    });

    // 2. Extract parameters from the URL (e.g., /verify/:kind/:id)
    this.route.paramMap.subscribe(params => {
      const kindParam = params.get('kind');
      const idParam = params.get('id');

      if (kindParam === 'voter' || kindParam === 'candidate') {
        this.kind = kindParam;
      }
      if (idParam) {
        this.targetId = +idParam;
        this.loadTargetData();
      }
    });

    // 3. Start the countdown
    this.startTimer();
  }

  ngOnDestroy(): void {
    // Clear timer when user leaves the page to prevent memory leaks
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
    }
  }

  loadTargetData(): void {
    // TODO: Call your backend service to fetch the email associated with this ID and Kind
    // Mocking the data for demonstration:
    this.targetEmail = this.kind === 'voter' ? 'voter@example.com' : 'candidate@example.com';
  }

  startTimer(): void {
    this.timerInterval = setInterval(() => {
      if (this.secondsLeft > 0) {
        this.secondsLeft--;
      } else {
        clearInterval(this.timerInterval);
        this.messages = ['Your verification code has expired. Please request a new one.'];
        this.verifyForm.get('otp')?.disable();
      }
    }, 1000);
  }

  resendCode(): void {
    this.api.verify(this.kind, this.targetId, { resend: true }).subscribe({
      next: () => {
        this.messages = ['A new code has been sent to your email.'];
        this.secondsLeft = 300; 
        this.verifyForm.get('otp')?.enable();
        this.verifyForm.reset();
        clearInterval(this.timerInterval);
        this.startTimer();
      },
      error: err => {
        const msg = err?.error?.error || 'Unable to resend code.';
        this.messages = [msg];
      }
    });
  }

  onSubmit(): void {
    if (!this.verifyForm.valid || this.secondsLeft <= 0) {
      this.messages = ['Please enter a valid 6-digit code.'];
      return;
    }

    const otpValue = this.verifyForm.value.otp;
    this.api.verify(this.kind, this.targetId, { otp: otpValue }).subscribe({
      next: () => {
        this.messages = ['Verification successful!'];
        setTimeout(() => this.router.navigate(['/admin-dashboard']), 1500);
      },
      error: err => {
        const msg = err?.error?.error || 'Invalid or expired verification code.';
        this.messages = [msg];
      }
    });
  }

}