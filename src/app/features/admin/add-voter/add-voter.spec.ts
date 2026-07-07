import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { AddVoterComponent } from './add-voter';

describe('AddVoterComponent', () => {
  let component: AddVoterComponent;
  let fixture: ComponentFixture<AddVoterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddVoterComponent, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(AddVoterComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
