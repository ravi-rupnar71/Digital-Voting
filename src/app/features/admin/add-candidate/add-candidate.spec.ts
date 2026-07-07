import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { AddCandidateComponent } from './add-candidate';

describe('AddCandidateComponent', () => {
  let component: AddCandidateComponent;
  let fixture: ComponentFixture<AddCandidateComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddCandidateComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(AddCandidateComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
