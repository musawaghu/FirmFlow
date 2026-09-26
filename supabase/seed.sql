-- FIRM FLOW demo seed: Studio Meridian Architects
-- Synthetic data. All people, emails, and projects are fictional.
-- Run after schema.sql.
--
-- IDs are fixed so the demo, tests, and sample manual can refer to them:
--   firm      5e000000-0000-4000-8000-000000000001
--   people    5e000000-0000-4000-8000-0000000001NN
--   projects  5e000000-0000-4000-8000-0000000002NN
--
-- Demo scenarios this data supports:
--   * Payroll question -> Tom Brennan is out of office, card shows backup Grace Liu.
--   * "Who is the design manager for Riverside Library?" -> Rachel Adeyemi.
--   * "Who is responsible for BIM?" -> Samir Haddad.
--   * No confident match -> default contact Priya Raman (Office Manager).

begin;

-- ---------------------------------------------------------------------------
-- Firm
-- ---------------------------------------------------------------------------

insert into firms (id, name, slug, timezone) values
  ('5e000000-0000-4000-8000-000000000001', 'Studio Meridian Architects', 'studio-meridian', 'America/Los_Angeles');

-- ---------------------------------------------------------------------------
-- People (backups set in a second pass)
-- ---------------------------------------------------------------------------

insert into people
  (id, firm_id, full_name, title, department, email, phone_ext, work_days, work_start, work_end, is_out_of_office, out_of_office_until)
values
  -- Leadership
  ('5e000000-0000-4000-8000-000000000101', '5e000000-0000-4000-8000-000000000001', 'Dana Whitfield',  'Managing Principal',             'Leadership',      'dana.whitfield@studiomeridian.example',  '101', '{1,2,3,4,5}', '08:30', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000102', '5e000000-0000-4000-8000-000000000001', 'Marcus Oyelaran', 'Design Principal',               'Leadership',      'marcus.oyelaran@studiomeridian.example', '102', '{1,2,3,4,5}', '09:00', '18:00', false, null),
  -- Operations, HR, finance
  ('5e000000-0000-4000-8000-000000000103', '5e000000-0000-4000-8000-000000000001', 'Priya Raman',     'Office Manager',                 'Operations',      'priya.raman@studiomeridian.example',     '110', '{1,2,3,4,5}', '08:00', '16:30', false, null),
  ('5e000000-0000-4000-8000-000000000104', '5e000000-0000-4000-8000-000000000001', 'Elena Kowalski',  'HR Manager',                     'Human Resources', 'elena.kowalski@studiomeridian.example',  '111', '{1,2,3,4,5}', '08:30', '17:00', false, null),
  ('5e000000-0000-4000-8000-000000000105', '5e000000-0000-4000-8000-000000000001', 'Tom Brennan',     'Payroll & Accounting Manager',   'Finance',         'tom.brennan@studiomeridian.example',     '120', '{1,2,3,4,5}', '08:00', '16:30', true,  '2026-10-09'),
  ('5e000000-0000-4000-8000-000000000106', '5e000000-0000-4000-8000-000000000001', 'Grace Liu',       'Accounting Specialist',          'Finance',         'grace.liu@studiomeridian.example',       '121', '{1,2,3,4}',   '08:00', '16:30', false, null),
  ('5e000000-0000-4000-8000-000000000118', '5e000000-0000-4000-8000-000000000001', 'Fatima Noor',     'Studio Coordinator',             'Operations',      'fatima.noor@studiomeridian.example',     '112', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  -- Technology
  ('5e000000-0000-4000-8000-000000000107', '5e000000-0000-4000-8000-000000000001', 'Samir Haddad',    'BIM Manager',                    'Technology',      'samir.haddad@studiomeridian.example',    '130', '{1,2,3,4,5}', '08:30', '17:00', false, null),
  ('5e000000-0000-4000-8000-000000000108', '5e000000-0000-4000-8000-000000000001', 'Keiko Tanaka',    'BIM Coordinator',                'Technology',      'keiko.tanaka@studiomeridian.example',    '131', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000109', '5e000000-0000-4000-8000-000000000001', 'Luis Ortega',     'IT Manager',                     'Technology',      'luis.ortega@studiomeridian.example',     '140', '{1,2,3,4,5}', '08:00', '17:00', false, null),
  ('5e000000-0000-4000-8000-000000000110', '5e000000-0000-4000-8000-000000000001', 'Jordan Pike',     'IT Support Specialist',          'Technology',      'jordan.pike@studiomeridian.example',     '141', '{1,2,3,4,5}', '07:30', '16:00', false, null),
  -- Studio
  ('5e000000-0000-4000-8000-000000000111', '5e000000-0000-4000-8000-000000000001', 'Rachel Adeyemi',  'Design Manager',                 'Studio',          'rachel.adeyemi@studiomeridian.example',  '150', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000112', '5e000000-0000-4000-8000-000000000001', 'Omar Siddiqui',   'Design Manager',                 'Studio',          'omar.siddiqui@studiomeridian.example',   '151', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000113', '5e000000-0000-4000-8000-000000000001', 'Hannah Morrow',   'Senior Project Manager',         'Studio',          'hannah.morrow@studiomeridian.example',   '152', '{1,2,3,4,5}', '08:30', '17:00', false, null),
  ('5e000000-0000-4000-8000-000000000114', '5e000000-0000-4000-8000-000000000001', 'Victor Hale',     'Project Manager',                'Studio',          'victor.hale@studiomeridian.example',     '153', '{1,2,3,4,5}', '08:30', '17:00', false, null),
  ('5e000000-0000-4000-8000-000000000115', '5e000000-0000-4000-8000-000000000001', 'Ben Castillo',    'Project Architect',              'Studio',          'ben.castillo@studiomeridian.example',    '160', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000116', '5e000000-0000-4000-8000-000000000001', 'Chloe Bennett',   'Senior Designer',                'Studio',          'chloe.bennett@studiomeridian.example',   '161', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000117', '5e000000-0000-4000-8000-000000000001', 'Nate Olsen',      'Architectural Designer',         'Studio',          'nate.olsen@studiomeridian.example',      '162', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000119', '5e000000-0000-4000-8000-000000000001', 'Alex Rivera',     'Architectural Intern',           'Studio',          'alex.rivera@studiomeridian.example',     '170', '{1,2,3,4,5}', '09:00', '17:30', false, null),
  ('5e000000-0000-4000-8000-000000000120', '5e000000-0000-4000-8000-000000000001', 'Jamie Cho',       'Architectural Intern',           'Studio',          'jamie.cho@studiomeridian.example',       '171', '{1,2,3,4,5}', '09:00', '17:30', false, null);

-- Backup contacts (shown on the card when the primary is out)
update people as p set backup_person_id = b.backup
from (values
  ('5e000000-0000-4000-8000-000000000101'::uuid, '5e000000-0000-4000-8000-000000000102'::uuid),  -- Dana -> Marcus
  ('5e000000-0000-4000-8000-000000000102'::uuid, '5e000000-0000-4000-8000-000000000101'::uuid),  -- Marcus -> Dana
  ('5e000000-0000-4000-8000-000000000103'::uuid, '5e000000-0000-4000-8000-000000000118'::uuid),  -- Priya -> Fatima
  ('5e000000-0000-4000-8000-000000000104'::uuid, '5e000000-0000-4000-8000-000000000103'::uuid),  -- Elena -> Priya
  ('5e000000-0000-4000-8000-000000000105'::uuid, '5e000000-0000-4000-8000-000000000106'::uuid),  -- Tom -> Grace
  ('5e000000-0000-4000-8000-000000000106'::uuid, '5e000000-0000-4000-8000-000000000105'::uuid),  -- Grace -> Tom
  ('5e000000-0000-4000-8000-000000000118'::uuid, '5e000000-0000-4000-8000-000000000103'::uuid),  -- Fatima -> Priya
  ('5e000000-0000-4000-8000-000000000107'::uuid, '5e000000-0000-4000-8000-000000000108'::uuid),  -- Samir -> Keiko
  ('5e000000-0000-4000-8000-000000000108'::uuid, '5e000000-0000-4000-8000-000000000107'::uuid),  -- Keiko -> Samir
  ('5e000000-0000-4000-8000-000000000109'::uuid, '5e000000-0000-4000-8000-000000000110'::uuid),  -- Luis -> Jordan
  ('5e000000-0000-4000-8000-000000000110'::uuid, '5e000000-0000-4000-8000-000000000109'::uuid),  -- Jordan -> Luis
  ('5e000000-0000-4000-8000-000000000111'::uuid, '5e000000-0000-4000-8000-000000000112'::uuid),  -- Rachel -> Omar
  ('5e000000-0000-4000-8000-000000000112'::uuid, '5e000000-0000-4000-8000-000000000111'::uuid),  -- Omar -> Rachel
  ('5e000000-0000-4000-8000-000000000113'::uuid, '5e000000-0000-4000-8000-000000000114'::uuid),  -- Hannah -> Victor
  ('5e000000-0000-4000-8000-000000000114'::uuid, '5e000000-0000-4000-8000-000000000113'::uuid)   -- Victor -> Hannah
) as b (person, backup)
where p.id = b.person;

update firms
set default_contact_id = '5e000000-0000-4000-8000-000000000103'  -- Priya Raman, Office Manager
where id = '5e000000-0000-4000-8000-000000000001';

-- ---------------------------------------------------------------------------
-- Responsibilities ("who handles what")
-- ---------------------------------------------------------------------------

insert into responsibilities (firm_id, person_id, topic, description, keywords, is_personal, rank)
select '5e000000-0000-4000-8000-000000000001', person_id::uuid, topic, description, keywords, is_personal, rank
from (values
  -- Payroll and time
  ('5e000000-0000-4000-8000-000000000105', 'payroll', 'Paychecks, pay stubs, direct deposit, tax withholding, and W-2s.',
    '{payroll,paycheck,"pay stub",salary,"direct deposit",withholding,W-2,tax}'::text[], true, 1),
  ('5e000000-0000-4000-8000-000000000106', 'payroll', 'Backup for payroll questions.',
    '{payroll,paycheck,"pay stub","direct deposit"}'::text[], true, 2),
  ('5e000000-0000-4000-8000-000000000106', 'timesheets', 'Timesheet system access, corrections, and late or missing timesheets.',
    '{timesheet,timesheets,hours,Vantagepoint,"time entry","phase code",overtime}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000105', 'timesheets', 'Backup for timesheet questions.',
    '{timesheet,hours,Vantagepoint}'::text[], false, 2),
  ('5e000000-0000-4000-8000-000000000106', 'expenses', 'Expense reports, mileage, and reimbursements.',
    '{expense,expenses,mileage,reimbursement,receipt}'::text[], false, 1),

  -- HR
  ('5e000000-0000-4000-8000-000000000104', 'pto', 'PTO balances, time-off requests, holidays, and leave.',
    '{PTO,vacation,"time off","sick leave",holiday,leave,"day off"}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000103', 'pto', 'Backup for PTO questions.',
    '{PTO,vacation,"time off"}'::text[], false, 2),
  ('5e000000-0000-4000-8000-000000000104', 'benefits', 'Health, dental, vision, 401(k), and other benefits.',
    '{benefits,insurance,health,dental,vision,401k,FSA,enrollment}'::text[], true, 1),
  ('5e000000-0000-4000-8000-000000000104', 'harassment_reporting', 'Reports of harassment, discrimination, or retaliation.',
    '{harassment,discrimination,retaliation,complaint,misconduct,report,unsafe}'::text[], true, 1),
  ('5e000000-0000-4000-8000-000000000101', 'harassment_reporting', 'Any principal may also receive a report.',
    '{harassment,discrimination,retaliation,complaint}'::text[], true, 2),
  ('5e000000-0000-4000-8000-000000000118', 'training', 'Onboarding schedule, required trainings (including harassment prevention), and continuing education.',
    '{training,onboarding,"harassment training",CE,AIA,licensure,ARE,orientation}'::text[], false, 1),

  -- Privacy and IT
  ('5e000000-0000-4000-8000-000000000109', 'privacy', 'Client confidentiality, NDAs, data handling, and reporting lost devices or data exposure.',
    '{privacy,confidential,NDA,"client data","data breach","lost laptop",security}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000104', 'privacy', 'Employee personal information and HR records.',
    '{privacy,"personal information","HR records"}'::text[], true, 2),
  ('5e000000-0000-4000-8000-000000000110', 'it_support', 'Computers, accounts, passwords, VPN, printers, plotters, and software installs.',
    '{IT,computer,laptop,password,VPN,email,printer,plotter,software,install,monitor}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000109', 'it_support', 'Backup for IT support.',
    '{IT,computer,password,VPN}'::text[], false, 2),

  -- BIM
  ('5e000000-0000-4000-8000-000000000107', 'bim', 'BIM standards, Revit templates, worksharing, central models, and BIM execution plans.',
    '{BIM,Revit,worksharing,"central model",template,"execution plan",Navisworks,model}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000108', 'bim', 'Backup for BIM questions.',
    '{BIM,Revit,worksharing}'::text[], false, 2),
  ('5e000000-0000-4000-8000-000000000108', 'revit_content', 'Revit families, keynote file, title blocks, and the content library.',
    '{families,keynotes,keynote,"title block","content library",family}'::text[], false, 1),

  -- Office and studio
  ('5e000000-0000-4000-8000-000000000103', 'office', 'Building access, key cards, parking, desks, supplies, mail, and the kitchen.',
    '{office,"key card",access,parking,desk,supplies,mail,kitchen,building}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000113', 'staffing', 'Project assignments and workload.',
    '{staffing,assignment,workload,"which project",capacity}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000102', 'design_review', 'Studio design reviews and pin-ups.',
    '{"design review",pin-up,crit,critique}'::text[], false, 1),
  ('5e000000-0000-4000-8000-000000000102', 'project_imagery', 'Approval to share project images publicly, including social media.',
    '{"social media",instagram,linkedin,portfolio,photos,renderings,images}'::text[], false, 1)
) as r (person_id, topic, description, keywords, is_personal, rank);

-- ---------------------------------------------------------------------------
-- Projects and roles
-- ---------------------------------------------------------------------------

insert into projects (id, firm_id, code, name, client, phase, location) values
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000001', 'RL-2301', 'Riverside Library',                   'City of Riverside Public Library', 'Construction Documents',   'Riverside'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000001', 'HP-2204', 'Harbor Point Mixed-Use',              'Harborline Development LLC',       'Design Development',       'Harbor District'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000001', 'CH-2402', 'Cedar Hills Elementary Modernization', 'Cedar Hills School District',      'Schematic Design',         'Cedar Hills'),
  ('5e000000-0000-4000-8000-000000000204', '5e000000-0000-4000-8000-000000000001', 'FS-2105', 'Fire Station 7',                      'Riverside Fire Department',        'Construction Administration', 'Riverside');

insert into project_roles (project_id, person_id, role) values
  -- Riverside Library
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000101', 'principal_in_charge'),
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000111', 'design_manager'),
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000113', 'project_manager'),
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000115', 'project_architect'),
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000108', 'bim_lead'),
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000117', 'designer'),
  ('5e000000-0000-4000-8000-000000000201', '5e000000-0000-4000-8000-000000000119', 'intern'),
  -- Harbor Point Mixed-Use
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000102', 'principal_in_charge'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000112', 'design_manager'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000114', 'project_manager'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000116', 'project_architect'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000107', 'bim_lead'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000117', 'designer'),
  ('5e000000-0000-4000-8000-000000000202', '5e000000-0000-4000-8000-000000000120', 'intern'),
  -- Cedar Hills Elementary Modernization
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000101', 'principal_in_charge'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000111', 'design_manager'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000113', 'project_manager'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000115', 'project_architect'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000108', 'bim_lead'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000116', 'designer'),
  ('5e000000-0000-4000-8000-000000000203', '5e000000-0000-4000-8000-000000000120', 'intern'),
  -- Fire Station 7
  ('5e000000-0000-4000-8000-000000000204', '5e000000-0000-4000-8000-000000000102', 'principal_in_charge'),
  ('5e000000-0000-4000-8000-000000000204', '5e000000-0000-4000-8000-000000000112', 'design_manager'),
  ('5e000000-0000-4000-8000-000000000204', '5e000000-0000-4000-8000-000000000114', 'project_manager'),
  ('5e000000-0000-4000-8000-000000000204', '5e000000-0000-4000-8000-000000000116', 'project_architect'),
  ('5e000000-0000-4000-8000-000000000204', '5e000000-0000-4000-8000-000000000107', 'bim_lead');

commit;

-- ---------------------------------------------------------------------------
-- Demo logins (run after creating the auth users)
-- ---------------------------------------------------------------------------
-- profiles.id must match an auth.users id, so create these two users first in
-- Supabase Dashboard -> Authentication -> Add user, then run the inserts below.
--
--   priya.raman@studiomeridian.example   (admin)
--   alex.rivera@studiomeridian.example   (employee, the demo intern)
--
-- insert into profiles (id, firm_id, person_id, role, full_name, email, start_date)
-- select u.id, '5e000000-0000-4000-8000-000000000001', p.id, v.role::user_role, p.full_name, p.email, v.start_date::date
-- from (values
--   ('priya.raman@studiomeridian.example', 'admin',    '2019-03-04'),
--   ('alex.rivera@studiomeridian.example', 'employee', '2026-09-28')
-- ) as v (email, role, start_date)
-- join auth.users u on u.email = v.email
-- join people p on p.email = v.email;
