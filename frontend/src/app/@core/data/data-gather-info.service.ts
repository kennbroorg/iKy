import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable } from '@angular/core';

// Dialog
import { NbDialogService } from '@nebular/theme';
import { ModalDialogComponent } from '../../pages/shared/modal-dialog/modal-dialog.component';

// RxJS
import { takeWhile } from 'rxjs/operators' ;
import { Observable } from 'rxjs/Observable';
import { mergeMap } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

// Toaster 
import { ToasterConfig } from 'angular2-toaster';
import 'style-loader!angular2-toaster/toaster.css';
import { NbGlobalLogicalPosition, NbGlobalPhysicalPosition, NbGlobalPosition, NbToastrService } from '@nebular/theme';
import { NbToastStatus } from '@nebular/theme/components/toastr/model';

@Injectable({
    providedIn: 'root'
})
export class DataGatherInfoService {  
      
    private data = {};  
    private globalGather: any = {};  
        
    private email: string;
    private username: string;
    public  response: any;
    private visualTasks: any;
    
    constructor(private http: HttpClient,
                private dialogService: NbDialogService,
                private toastrService: NbToastrService) {}
    
    /* Global Data */
    public initialize() {  
        this.globalGather = {};
        console.log('dataService Initialize globalGather :', this.globalGather)
        return this.globalGather;
    }  
    
    public pushGather(key, value) {  
        this.globalGather[key] = value;
        console.log('dataService Push globalGather :', this.globalGather)
    }  
    
    public pullGather() {  
        console.log('dataService Pull globalGather :', this.globalGather)
        return this.globalGather;
    }  
    
    /* Http Service */
    // private readonly gatherUrl: string = environment.apiUrl + 'pub/items';
    // TODO : Use environment to set gatherUrl
    private readonly gatherUrl: string = 'http://127.0.0.1:5000/';
    
    // Get test
    public postTest$(): Observable<any> {
        return this.http.post<any>(this.gatherUrl + 'testing', 1);
    }
    
    // Get tasklist
    public getTaskList$(): Observable<any> {
        return this.http.get<any>(this.gatherUrl + 'tasklist');
    }
    
    // Get apikeys
    public getApiKeys$(keys: any): Observable<any> {
        return this.http.post<any>(this.gatherUrl + 'apikey', keys);
    }
    
    // Generic GET request
    public getRequest$(url: string): Observable<any> {
        return this.http.get<any>(this.gatherUrl + url);
    }

    // Generic POST request
    public postRequest$(module: string, param: any): Observable<any> {
        return this.http.post<any>(this.gatherUrl + module, param);
    }
    
    // Generic POST and GET request
    public executeRequest$(module: string, param: any): Observable<any> {
        return this.http.post<any>(this.gatherUrl + module, param)
                   .pipe(mergeMap(task => this.getRequestResult$('result/' + task.task, task)));
    }
    // GET request result
    public getRequestResult$(url: string, task: any): Observable<any> {
        this.globalGather['taskexec'].push({"module" : task.module, "param" : task.param,
                      "task_id" : task.task, "state" : "PENDING", "from" : task.from_m});
        return this.http.get<any>(this.gatherUrl + url);
    }

    // Is the email valid format
    public isValidFormatEmail(email) {
        var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }
    
    // Validate email
    public validateEmail(email) {
        console.log("validateEmail func", email);
        if (this.isValidFormatEmail(email)) {
            // Execute gatherer 
            this.pushGather('email', email);
            this.gathererInfo(email); 
        } else {
            // Launch Dialog
            this.openDialog();
        }
        return this.globalGather;
    }
    
    /* Dialog */
    public openDialog() {
        this.dialogService.open(ModalDialogComponent, {
            context: {
                title: 'Invalid e-mail',
                text: 'You must enter a valid e-mail address to gather information',
            },
            hasBackdrop: true,
        });
    }

    /* Gather Info */
    public gathererInfo(email: string) {
    
        this.email = email;
        // Split email in username and domain
        this.username = email.split("@")[0];
        this.globalGather['taskexec'] = [];
        console.log("Username : ", this.username);
    
        // Generic executer
        this.showToast(NbToastStatus.INFO, 'Tasklist', 'Send Tasklist process');
        this.getTaskList$()
            .subscribe(this.processTasklist, 
                       err => console.error('Ops: ', err.message)
        );
        
        // EmailRepIO
        this.showToast(NbToastStatus.INFO, 'EmailRepIO', 'Send information gathering');
        this.executeRequest$('emailrep', {username: this.email, from: 'Initial'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed EmailRep')
        );

        // Fullcontact
        if (this.isModuleParamRun('fullcontact', this.email, 'Initial')) {
            this.showToast(NbToastStatus.INFO, 'Fullcontact', 'Send information gathering');
            this.executeRequest$('fullcontact', {username: this.email, from: 'Initial'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Fullcontact')
            );
        };
    
        // Github
        if (this.isModuleParamRun('github', this.username, 'Initial')) {
            this.showToast(NbToastStatus.INFO, 'GitHub', 'Send information gathering');
            this.executeRequest$('github', {username: this.username, from: 'Initial'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed GitHub')
            );
        };
    
        // // Ghostproject TODO : Repair
        // this.showToast(NbToastStatus.INFO, 'Ghostproject', 'Send information gathering');
        // this.executeRequest$('ghostproject', {username: this.email, from: 'Initial'})
        //         .subscribe(this.processResponse,
        //                    err => console.error('Ops: ', err.message),
        //                    () => console.log('Completed ghostproject')
        // );
    
        // Linkedin
        if (this.isModuleParamRun('linkedin', this.email, 'Initial')) {
            this.showToast(NbToastStatus.INFO, 'Linkedin', 'Send information gathering');
            this.executeRequest$('linkedin', {username: this.email, from: 'Initial'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed linkedin')
            );
        };
    
        // Keybase
        if (this.isModuleParamRun('keybase', this.username, 'Initial')) {
            this.showToast(NbToastStatus.INFO, 'Keybase', 'Send information gathering');
            this.executeRequest$('keybase', {username: this.username, from: 'Initial'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed keybase')
            );
        };
    
        // Leaks 
        this.showToast(NbToastStatus.INFO, 'Leaks (HIBP)', 'Send information gathering');
        this.executeRequest$('leaks', {username: this.email, from: 'Initial'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed leaks')
        );

        // SocialScan
        this.showToast(NbToastStatus.INFO, 'SocialScan', 'Send information gathering');
        this.executeRequest$('socialscan', {username: this.email, from: 'Initial'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed SocialScan')
        );

    }
    
    // Tasklist Callback
    private processTasklist = (data: any): any => {
        this.globalGather['tasklist'] = data;
        // this.tasklist = data;
        this.showToast(NbToastStatus.SUCCESS, 'Tasklist', 'Process ended');
    };
    
    private isTaskImplemented(module) {
        let tasklist = this.globalGather['tasklist'].modules;
        for (let indexTasklist in tasklist) {
            if (tasklist[indexTasklist] == module) return true;
        }
        return false;
    }
    
    private isModuleParamRun(module, param, from) {
        // Validate if module run
        let taskexec = this.globalGather['taskexec'];
        let mustRun = true;
        for (let indexTaskexec in taskexec) {
            // if (module == 'linkedin' ||
            //     taskexec[indexTaskexec].module == module && 
            //     taskexec[indexTaskexec].param == param) {
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param == param) {
                mustRun = false;
            } 
        }
        // If Run modify validation
        return mustRun;
    }
    
    // Generic Callback
    private processResponse = (data: any): any => {
        this.response = data;
        let module_name = this.response.result[0].module;
        console.log('************************************************************************');
        console.log('Module :', module_name);
        console.log('************************************************************************');
    
        // Valitate tasks to exec others
        for (let index in this.response.result) {
            if (this.response.result[index].tasks && this.response.result[index].tasks.length > 0) {
                let tasks = this.response.result[index].tasks; 
                for (let indexTask in tasks) {
                    if (this.isTaskImplemented(tasks[indexTask].module)) {
                        console.log("Implemented : ", tasks[indexTask].module);
                        if (this.isModuleParamRun(tasks[indexTask].module, 
                                                  tasks[indexTask].param,
                                                  module_name)) {
                            // Execute another tasks
                            this.showToast(NbToastStatus.INFO, tasks[indexTask].module, 'Send information gathering');
                            this.executeRequest$(tasks[indexTask].module, {username: tasks[indexTask].param, from: module_name})
                                    .subscribe(this.processResponse,
                                               err => console.error('Ops: ', err.message),
                                               () => console.log('Completed' + tasks[indexTask].module)
                            );
                        }
                    }
                }
            }
        }
    
        this.showToast(NbToastStatus.SUCCESS, module_name, 'Gather ended');
        this.globalGather[module_name] = data;
        console.log('Gathered :', this.globalGather);
    };
    
    // Toaster 
    private showToast(type: NbToastStatus, title: string, body: string) {
    
        config: ToasterConfig;
        const config = {
            status: type,
            destroyByClick: true,
            duration: 4000,
            hasIcon: true,
            position: NbGlobalPhysicalPosition.TOP_RIGHT,
            preventDuplicates: true,
        };
        // const titleContent = title ? `${title}` : '';
        
        this.toastrService.show(
            body,
            title,
            config);
    }

}  
