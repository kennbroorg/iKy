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

// Toaster KKK
import { ToasterConfig } from 'angular2-toaster';
import 'style-loader!angular2-toaster/toaster.css';
import { NbGlobalLogicalPosition, NbGlobalPhysicalPosition, NbGlobalPosition, NbToastrService, NbComponentStatus } from '@nebular/theme';
// import { NbToastStatus } from '@nebular/theme/components/toastr/model';

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
        for (let indexTaskexec in this.globalGather['taskexec']) {
            if (this.globalGather['taskexec'][indexTaskexec].module == task.module && 
                this.globalGather['taskexec'][indexTaskexec].param == task.param) {

                this.globalGather['taskexec'][indexTaskexec].task_id = task.task;
                this.globalGather['taskexec'][indexTaskexec].state = "PROCESS";
                console.log("State change..................");

            } 
        }
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
            // this.fakeGather(); 
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
        this.showToast('info', 'Tasklist', 'Send Tasklist process');
        this.getTaskList$()
            .subscribe(this.processTasklist, 
                       err => console.error('Ops: ', err.message)
        );
        
        // EmailRepIO
        if (this.isModuleParamRunTaskExec('emailrep', this.email, 'User', 100)) {
            // KKK this.showToast(NbToastStatus.INFO, 'EmailRepIO', 'Send information gathering');
            this.showToast('info', 'EmailRepIO', 'Send information gathering');
            this.executeRequest$('emailrep', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed EmailRep')
            );
        };

        // Search
        if (this.isModuleParamRunTaskExec('search', this.username, 'Username', 1)) {
            this.showToast('info', 'Searchers', 'Send information gathering');
            this.executeRequest$('search', {username: this.username, from: 'Username'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed Searchers')
            );
        };

        // Fullcontact
        if (this.isModuleParamRunTaskExec('fullcontact', this.email, 'User', 100)) {
            this.showToast('info', 'Fullcontact', 'Send information gathering');
            this.executeRequest$('fullcontact', {username: this.email, from: 'User'})
                .subscribe(this.processResponse,
                           err => console.error('Ops: ', err.message),
                           () => console.log('Completed Fullcontact')
            );
        };
    
        // Github
        if (this.isModuleParamRunTaskExec('github', this.username, 'Username', 1)) {
            this.showToast('info', 'GitHub', 'Send information gathering');
            this.executeRequest$('github', {username: this.username, from: 'Username'})
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
    
        // Linkedin TODO : This doesn't work anymore with mail
        // if (this.isModuleParamRunTaskExec('linkedin', this.email, 'User', 100)) {
        //     this.showToast(NbToastStatus.INFO, 'Linkedin', 'Send information gathering');
        //     this.executeRequest$('linkedin', {username: this.email, from: 'User'})
        //             .subscribe(this.processResponse,
        //                        err => console.error('Ops: ', err.message),
        //                        () => console.log('Completed linkedin')
        //     );
        // };
    
        // Keybase
        if (this.isModuleParamRunTaskExec('keybase', this.username, 'Username', 1)) {
            this.showToast('info', 'Keybase', 'Send information gathering');
            this.executeRequest$('keybase', {username: this.username, from: 'Username'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Keybase')
            );
        };
    
        // Leaks 
        if (this.isModuleParamRunTaskExec('leaks', this.email, 'User', 100)) {
            this.showToast('info', 'Leaks (HIBP)', 'Send information gathering');
            this.executeRequest$('leaks', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Leaks (HIBP)')
            );
        };

        // SocialScan
        if (this.isModuleParamRunTaskExec('socialscan', this.email, 'User', 100)) {
            this.showToast('info', 'SocialScan', 'Send information gathering');
            this.executeRequest$('socialscan', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed SocialScan')
            );
        };

    }

    /* Gather Info Advance */
    public gathererInfoAdvance(data: string) {

        this.pushGather('data', data);
        this.pushGather('email', data); // Temporary fix
        var datas = data;
        this.globalGather['taskexec'] = [];
        console.log("====================================================");
        console.log("Datas : ", datas);

        // Generic executer
        this.showToast('info', 'Tasklist', 'Send Tasklist process');
        this.getTaskList$()
            .subscribe(this.processTasklist, 
                       err => console.error('Ops: ', err.message)
        );
        
        // Evaluation of datas
        if (datas['twitter'] != '') {
            console.log("Twitter : ", datas['twitter']);
            // Twitter
            if (this.isModuleParamRunTaskExec('twitter', datas['twitter'], 'User', 100)) {
                this.showToast('info', 'Twitter', 'Send information gathering');
                this.executeRequest$('twitter', {username: datas['twitter'], from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed twitter')
                );
            };
        };
        
        if (datas['linkedin'] != '') {
            console.log("Linkedin : ", datas['linkedin']);
            // Linkedin
            if (this.isModuleParamRunTaskExec('linkedin', datas['linkedin'], 'User', 100)) {
                this.showToast('info', 'Linkedin', 'Send information gathering');
                this.executeRequest$('linkedin', {username: datas['linkedin'], from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Linkedin')
                );
            };
        };
        
        if (datas['github'] != '') {
            console.log("Github : ", datas['github']);
            // Github
            if (this.isModuleParamRunTaskExec('github', datas['github'], 'User', 100)) {
                this.showToast('info', 'Github', 'Send information gathering');
                this.executeRequest$('github', {username: datas['github'], from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Github')
                );
            };
        };
        
        if (datas['instagram'] != '') {
            console.log("Instagram : ", datas['instagram']);
            // Instagram
            if (this.isModuleParamRunTaskExec('instagram', datas['instagram'], 'User', 100)) {
                this.showToast('info', 'Instagram', 'Send information gathering');
                this.executeRequest$('instagram', {username: datas['instagram'], from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Instagram')
                );
            };
        };
        
        if (datas['tiktok'] != '') {
            console.log("Tiktok : ", datas['tiktok']);
            // Tiktok
            if (this.isModuleParamRunTaskExec('tiktok', datas['tiktok'], 'User', 100)) {
                this.showToast('info', 'TikTok', 'Send information gathering');
                this.executeRequest$('tiktok', {username: datas['tiktok'], from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Tiktok')
                );
            };
        };
        
        if (datas['email'] != '') {
            console.log("Email : ", datas['email']);

            this.email = datas['email'];
            // Split email in username and domain
            this.username = datas['email'].split("@")[0];
            console.log("Username : ", this.username);

            if (this.isModuleParamRunTaskExec('emailrep', this.email, 'User', 100)) {
                this.showToast('info', 'EmailRepIO', 'Send information gathering');
                this.executeRequest$('emailrep', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed EmailRep')
                );
            };

            // Search
            if (this.isModuleParamRunTaskExec('search', this.username, 'Username', 1)) {
                this.showToast('info', 'Searchers', 'Send information gathering');
                this.executeRequest$('search', {username: this.username, from: 'Username'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Searchers')
                );
            };

            // Fullcontact
            if (this.isModuleParamRunTaskExec('fullcontact', this.email, 'User', 100)) {
                this.showToast('info', 'Fullcontact', 'Send information gathering');
                this.executeRequest$('fullcontact', {username: this.email, from: 'User'})
                    .subscribe(this.processResponse,
                               err => console.error('Ops: ', err.message),
                               () => console.log('Completed Fullcontact')
                );
            };
    
            // Github
            if (this.isModuleParamRunTaskExec('github', this.username, 'Username', 1)) {
                this.showToast('info', 'GitHub', 'Send information gathering');
                this.executeRequest$('github', {username: this.username, from: 'Username'})
                        .subscribe(this.processResponse,
                                   err => console.error('Ops: ', err.message),
                                   () => console.log('Completed GitHub')
                );
            };

            // Linkedin TODO : This doesn't work anymore with mail
            if (this.isModuleParamRunTaskExec('linkedin', this.email, 'User', 100)) {
                this.showToast('info', 'Linkedin', 'Send information gathering');
                this.executeRequest$('linkedin', {username: this.email, from: 'User'})
                        .subscribe(this.processResponse,
                                   err => console.error('Ops: ', err.message),
                                   () => console.log('Completed linkedin')
                );
            };
    
            // Keybase
            if (this.isModuleParamRunTaskExec('keybase', this.username, 'Username', 1)) {
                this.showToast('info', 'Keybase', 'Send information gathering');
                this.executeRequest$('keybase', {username: this.username, from: 'Username'})
                        .subscribe(this.processResponse,
                                   err => console.error('Ops: ', err.message),
                                   () => console.log('Completed Keybase')
                );
            };
    
            // Leaks 
            if (this.isModuleParamRunTaskExec('leaks', this.email, 'User', 100)) {
                this.showToast('info', 'Leaks (HIBP)', 'Send information gathering');
                this.executeRequest$('leaks', {username: this.email, from: 'User'})
                        .subscribe(this.processResponse,
                                   err => console.error('Ops: ', err.message),
                                   () => console.log('Completed Leaks (HIBP)')
                );
            };

            // SocialScan
            if (this.isModuleParamRunTaskExec('socialscan', this.email, 'User', 100)) {
                this.showToast('info', 'SocialScan', 'Send information gathering');
                this.executeRequest$('socialscan', {username: this.email, from: 'User'})
                        .subscribe(this.processResponse,
                                   err => console.error('Ops: ', err.message),
                                   () => console.log('Completed SocialScan')
                );
            };
        };
    }
    
    // Tasklist Callback
    private processTasklist = (data: any): any => {
        this.globalGather['tasklist'] = data;
        // this.tasklist = data;
        this.showToast('success', 'Tasklist', 'Process ended');
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
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param == param) {
                mustRun = false;
            } 
        }
        return mustRun;
    }
    
    private isModuleParamRunTaskExec(module, param, from, score) {
        // Validate if module run
        let taskexec = this.globalGather['taskexec'];
        let mustRun = true;

        // Priority
        if (from == 'search') {
            score = 5;
        }


        for (let indexTaskexec in taskexec) {

            // Evaluate module == / param <> / from <> "User"
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param != param && 
                from != "User") {
                mustRun = false; // Not run
            } 
            // Evaluate module == / param <> / score > score
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param != param && 
                taskexec[indexTaskexec].score > score) {
                mustRun = false; // Not run
            } 
            // Evaluate module
            if (taskexec[indexTaskexec].module == module && 
                taskexec[indexTaskexec].param == param) {
                mustRun = false; // Not run

                console.log('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
                console.log('Module :', module);
                console.log('Param  :', param);
                console.log('From   :', from);
                console.log('Score  :', score);
                console.log('Score Before :', this.globalGather['taskexec'][indexTaskexec].score);

                this.globalGather['taskexec'][indexTaskexec].score = taskexec[indexTaskexec].score + score;
                console.log('Score After :', this.globalGather['taskexec'][indexTaskexec].score);
                console.log('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!');
            } 
        }
        // Evaluate if run
        if (mustRun) {
            this.globalGather['taskexec'].push({"module" : module, "param" : param,
                 "state" : "PENDING", "from" : from, "score": score});
        }
        return mustRun;
    }
    
    // Generic Callback
    private processResponse = (data: any): any => {
        this.response = data;
        let module_name = this.response.result[0].module;
        let param = this.response.result[1].param;
        console.log('************************************************************************');
        console.log('Module :', module_name);
        console.log('Param  :', param);
        console.log('************************************************************************');
    
        // Valitate tasks to exec others
        for (let index in this.response.result) {
            if (this.response.result[index].tasks && this.response.result[index].tasks.length > 0) {
                let tasks = this.response.result[index].tasks; 
                for (let indexTask in tasks) {
                    if (this.isTaskImplemented(tasks[indexTask].module)) {
                        console.log("Implemented : ", tasks[indexTask].module);
                        if (this.isModuleParamRunTaskExec(tasks[indexTask].module, 
                                                  tasks[indexTask].param,
                                                  module_name, 10)) {
                            // Execute another tasks
                            this.showToast('info', tasks[indexTask].module, 'Send information gathering');
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
    
        this.showToast('success', module_name, 'Gather ended');
        this.globalGather[module_name] = data;

        for (let indexTaskexec in this.globalGather['taskexec']) {
            if (this.globalGather['taskexec'][indexTaskexec].module == module_name && 
                this.globalGather['taskexec'][indexTaskexec].param == param) {

                this.globalGather['taskexec'][indexTaskexec].state = "SUCCESS";
                console.log("State change..................SUCCESS");
                console.log(this.globalGather[module_name].result[2].validation);

                // Reprocess validation
                if (this.globalGather['taskexec'][indexTaskexec].score > 99) {
                    this.globalGather[module_name].result[2].validation = "hard";
                } else if (this.globalGather['taskexec'][indexTaskexec].score > 9) {
                    this.globalGather[module_name].result[2].validation = "soft";
                } else {
                    this.globalGather[module_name].result[2].validation = "no";
                }

            } 
        }

        console.log('Gathered :', this.globalGather);
    };
    
    // Toaster 
    private showToast(type: NbComponentStatus, title: string, body: string) {
    
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
