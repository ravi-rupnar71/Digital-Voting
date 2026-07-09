import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { ApiService } from '../../../core/services/api';
import { AddCandidateComponent } from './add-candidate';

describe('AddCandidateComponent', () => {
  let component: AddCandidateComponent;
  let fixture: ComponentFixture<AddCandidateComponent>;
  let apiService: jasmine.SpyObj<ApiService>;
  let router: Router;

  beforeEach(async () => {
    const apiSpy = jasmine.createSpyObj('ApiService', ['addCandidate']);

    await TestBed.configureTestingModule({
      imports: [AddCandidateComponent, RouterTestingModule],
      providers: [{ provide: ApiService, useValue: apiSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(AddCandidateComponent);
    component = fixture.componentInstance;
    apiService = TestBed.inject(ApiService) as jasmine.SpyObj<ApiService>;
    router = TestBed.inject(Router);
    spyOn(router, 'navigate');
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should redirect to admin dashboard after candidate verification', () => {
    apiService.addCandidate.and.returnValue(of({ candidate_id: 7, verification_otp: '123456', email_sent: true }));
    component.candidateForm.setValue({
      name: 'Jane Doe',
      party: 'Green',
      email: 'jane@example.com',
      password: 'secret123'
    });

    component.onSubmit();

    expect(apiService.addCandidate).toHaveBeenCalled();
    expect(router.navigate).toHaveBeenCalledWith(
      ['/verify-email', 'candidate', 7],
      jasmine.objectContaining({
        state: jasmine.objectContaining({ redirectTo: '/admin-dashboard' })
      })
    );
  });
});
